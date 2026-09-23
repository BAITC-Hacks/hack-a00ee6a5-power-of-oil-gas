import json
from ..database import db_session
from .rating_service import calculate_score

SEED_CHALLENGES = [
    {
        "raw_description": "Снизить незапланированные простои насосного оборудования на основе сенсорных данных.",
        "industry": "Oil & Gas",
        "title": "Predictive Maintenance для насосов",
        "context": "Незапланированные отказы насосов приводят к простоям оборудования.",
        "need": "Нужно заранее выявлять риск неисправности.",
        "users": "Инженеры по надёжности и техническому обслуживанию.",
        "data_materials": "Температура, вибрация, давление и история ремонтов.",
        "constraints": "MVP должен работать на обезличенных данных.",
        "expected_result": "Прототип модели прогнозирования и простой dashboard.",
        "success_criteria": "Показать качество модели на тестовом наборе и объяснить метрики.",
        "contact": "Куратор бизнес-задачи.",
        "interaction_format": "Две консультации в неделю онлайн.",
    },
    {
        "raw_description": "Нужен цифровой помощник для адаптации новых сотрудников.",
        "industry": "HR",
        "title": "Digital Buddy для новых сотрудников",
        "context": "Новым сотрудникам трудно быстро находить регламенты и ответы на типовые вопросы.",
        "need": "Сократить время адаптации.",
        "users": "Новые сотрудники.",
        "data_materials": "FAQ и обезличенные внутренние инструкции.",
        "constraints": "Без персональных данных.",
        "expected_result": "Интерактивный прототип помощника.",
        "success_criteria": "Пользователь проходит 5 типовых сценариев без помощи HR.",
        "contact": "HR-куратор.",
        "interaction_format": "Еженедельная консультация.",
    },
    {
        "raw_description": "Хотим лучше понимать энергопотребление корпуса.",
        "industry": "Energy",
        "title": "Аналитика энергопотребления",
        "context": "Есть почасовые данные по энергопотреблению одного корпуса.",
        "need": "Найти пики и возможные точки экономии.",
        "users": "Служба эксплуатации.",
        "data_materials": "CSV с почасовыми значениями за 3 месяца.",
        "constraints": None,
        "expected_result": "Dashboard с аномалиями и основными выводами.",
        "success_criteria": "Выявлены и объяснены основные пики потребления.",
        "contact": "Инженер энергетик.",
        "interaction_format": None,
    },
    {
        "raw_description": "Нужно приложение для очередей.",
        "industry": "Smart City",
        "title": "Управление очередями",
        "context": None,
        "need": "Снизить время ожидания посетителей.",
        "users": None,
        "data_materials": None,
        "constraints": None,
        "expected_result": "Прототип интерфейса.",
        "success_criteria": None,
        "contact": None,
        "interaction_format": None,
    },
    {
        "raw_description": "Хотим AI для документов.",
        "industry": "Other",
        "title": "AI для документов",
        "context": None,
        "need": "Упростить работу с документами.",
        "users": None,
        "data_materials": None,
        "constraints": None,
        "expected_result": None,
        "success_criteria": None,
        "contact": None,
        "interaction_format": None,
    },
]

SEED_TEAMS = [
    ("AI Engineers", ["Oil & Gas", "AI"], ["Python", "Machine Learning", "Data Analysis"], ["FastAPI", "React", "scikit-learn"]),
    ("Data Pulse", ["Energy", "Analytics"], ["Python", "BI", "Statistics"], ["Pandas", "Power BI", "FastAPI"]),
    ("UX Forge", ["Smart City", "Education"], ["UX/UI", "Frontend", "Research"], ["React", "Figma", "Vite"]),
    ("Secure Minds", ["Cybersecurity", "FinTech"], ["Security", "Backend", "Python"], ["FastAPI", "PostgreSQL", "Docker"]),
    ("Vision Lab", ["AI", "Industry"], ["Computer Vision", "Python", "ML"], ["PyTorch", "OpenCV", "FastAPI"]),
]


def seed_if_empty():
    with db_session() as conn:
        if conn.execute("SELECT COUNT(*) FROM challenges").fetchone()[0] == 0:
            for item in SEED_CHALLENGES:
                rating = calculate_score(item, confirmed=True)
                conn.execute(
                    """
                    INSERT INTO challenges (
                        raw_description, industry, title, context, need, users, data_materials,
                        constraints_text, expected_result, success_criteria, contact,
                        interaction_format, score, readiness_level, status, is_confirmed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'published', 1)
                    """,
                    (
                        item["raw_description"], item["industry"], item["title"], item["context"],
                        item["need"], item["users"], item["data_materials"], item["constraints"],
                        item["expected_result"], item["success_criteria"], item["contact"],
                        item["interaction_format"], rating["score"], rating["readiness_level"],
                    ),
                )

        if conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 0:
            for name, interests, skills, technologies in SEED_TEAMS:
                conn.execute(
                    "INSERT INTO teams (name, interests, skills, technologies) VALUES (?, ?, ?, ?)",
                    (name, json.dumps(interests, ensure_ascii=False), json.dumps(skills, ensure_ascii=False), json.dumps(technologies, ensure_ascii=False)),
                )

        if conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 0:
            challenge_ids = [r[0] for r in conn.execute("SELECT id FROM challenges ORDER BY id LIMIT 5").fetchall()]
            team_rows = conn.execute("SELECT id, name FROM teams ORDER BY id LIMIT 5").fetchall()
            sample_ideas = [
                ("Соберём baseline и сравним несколько ML-подходов.", "EDA → baseline → validation → demo", "3 недели"),
                ("Сделаем интерактивный прототип с аналитикой.", "Исследование → прототип → пользовательский тест", "2 недели"),
                ("Построим dashboard и набор объяснимых метрик.", "Подготовка данных → метрики → dashboard", "10 дней"),
                ("Предлагаем быстрый web MVP с проверкой гипотезы.", "UX flow → backend → frontend → тест", "2 недели"),
                ("Проведём технический эксперимент и покажем сравнение решений.", "Данные → эксперимент → оценка → презентация", "3 недели"),
            ]
            for idx, (team_id, team_name) in enumerate(team_rows):
                if idx >= len(challenge_ids):
                    break
                idea, plan, deadline = sample_ideas[idx]
                conn.execute(
                    """
                    INSERT INTO proposals (
                        challenge_id, team_id, team_name, solution_idea, plan, deadline, prototype_url, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                    """,
                    (challenge_ids[idx], team_id, team_name, idea, plan, deadline, f"https://github.com/demo/team-{idx+1}"),
                )
