import sqlalchemy


engine = sqlalchemy.create_engine("sqlite:///.db", echo=True)
conn = engine.connect()
metadata = sqlalchemy.MetaData()
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True),
    sqlalchemy.Column("steam_url", sqlalchemy.Text, nullable=True),
    sqlalchemy.Column("dota_rating", sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column("about_me", sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(
        "sent_id", sqlalchemy.Integer, default=None, nullable=True, unique=True
    ),
)


metadata.create_all(engine)


def create_user(id: int):
    insertion_query = users.insert().values(
        [
            {"id": id},
        ]
    )
    print(f"created user with id {id}")
    conn.execute(insertion_query)
    conn.commit()


def set_steam_url(id: int, url: str):
    update_query = (
        sqlalchemy.update(users).where(users.columns.id == id).values(steam_url=url)
    )

    conn.execute(update_query)
    conn.commit()


def set_dota_rating(id: int, rating: int):
    update_query = (
        sqlalchemy.update(users)
        .where(users.columns.id == id)
        .values(dota_rating=rating)
    )

    conn.execute(update_query)
    conn.commit()


def set_about_me(id: int, data: str):
    update_query = (
        sqlalchemy.update(users).where(users.columns.id == id).values(about_me=data)
    )

    conn.execute(update_query)
    conn.commit()


def get_data_by_sent_id(sent_id: int):
    select_author_query = sqlalchemy.select(users).where(
        users.columns.sent_id == sent_id
    )
    select_all_results = conn.execute(select_author_query)
    return select_all_results.fetchone()


def approve_chel(id: int, message_id: int):
    update_query = (
        sqlalchemy.update(users)
        .where(users.columns.id == id)
        .values(sent_id=message_id)
    )
    conn.execute(update_query)
    conn.commit()


def get_data(id: int):
    select_author_query = sqlalchemy.select(users).where(users.columns.id == id)
    select_all_results = conn.execute(select_author_query)
    return select_all_results.fetchone()
