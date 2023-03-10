import asyncio
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv

import asyncpg

from utils import TERMS, write_to_file

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


db_params = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}


@asynccontextmanager
async def db_connection(**kwargs):
    conn = await asyncpg.connect(
        user=kwargs.get("user"),
        password=kwargs.get("password"),
        database=kwargs.get("database"),
        host=kwargs.get("host"),
        port=kwargs.get("port"),
    )
    yield conn
    await conn.close()


async def search_adwords_keywords(
    pool, term, columns, search_type="broad", total_keywords=1000
):
    separator = {"phrase": "<->", "broad": "&"}[search_type]
    q = f"{separator}".join(term.split(" "))

    search_query = f"""
        with matched_keywrods as (
            select *
            from adwords_en_us
            where keyword_tsv @@ to_tsquery('{q}')
        )
        select {', '.join(columns)}
        from matched_keywrods
        where spell_type is null
        order by volume desc
        limit {total_keywords};
    """

    async with pool.acquire() as conn:
        result = await conn.fetch(search_query)

    return [{col: r[col] for col in columns} for r in result]


async def run(terms, search_types, add_suffix, project):
    for term in terms:
        for search_type in search_types:
            print(f"<<<<<<<<< Search type: {search_type}, term: {term} >>>>>>>>>")
            t1 = time.perf_counter()
            result = await search_adwords_keywords(
                term, ["keyword", "volume"], search_type=search_type
            )
            print(f"Time taken, {term}: {time.perf_counter() - t1}")

            file_name = f"postgres/{project}/{term}_{search_type}" if add_suffix else f"postgres/{project}/{term}"
            write_to_file(file_name, result)


async def main(project='papi'):
    search_types = ["phrase", "broad"] if project == 'dapi' else ["broad"]
    add_suffix = project == 'dapi'

    await asyncio.gather(
        run(TERMS["singe_word_terms"], search_types, add_suffix, project),
        run(TERMS["two_word_terms"], search_types, add_suffix, project),
        run(TERMS["three_word_terms"], search_types, add_suffix, project),
    )


if __name__ == "__main__":
    asyncio.run(main())
