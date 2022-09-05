from importlib.metadata import metadata
from bot.db.base import engine
from sqlalchemy.sql import text
from sqlalchemy import MetaData, Table
from sqlalchemy_views import CreateView, DropView


drop_view_if_exist = text("DROP VIEW IF EXISTS whitelisted_hops_all")

# This view will display all hops path between two assets (start_denom, target_denom)
view_definition = text("""
            CREATE VIEW whitelisted_hops_all AS
            WITH RECURSIVE
            cte(start_denom, id , hops_len, target_denom, hops) AS (
            SELECT
                offer_denom AS start_denom,
                CAST(id AS TEXT) AS id,
                1 AS hops_len,
                ask_denom as target_denom,
                '<' || CAST(id AS TEXT) || '>' AS hops
            FROM whitelisted_hop
            UNION ALL
            SELECT
                ask_denom AS start_denom,
                'inverse-' || CAST(id AS TEXT) AS id,
                1 AS hops_len,
                offer_denom as target_denom,
                '<inverse-' || CAST(id AS TEXT) || '>' AS hops
            FROM whitelisted_hop
            UNION ALL
            SELECT
                start_denom,
                CAST(wh.id AS TEXT) AS id,
                hops_len + 1 AS hops_len,
                wh.ask_denom,
                cte.hops ||  CASE WHEN cte.target_denom=wh.offer_denom
                                   THEN '<'
                                   ELSE '<inverse-'
                               END || CAST(wh.id AS TEXT) || '>' AS hops
            FROM cte
                JOIN whitelisted_hop AS wh ON (cte.target_denom=wh.offer_denom
                or cte.target_denom = wh.ask_denom
                ) and (cte.hops NOT LIKE '%<' || CAST(wh.id AS TEXT) || '>%'
                                            and cte.hops NOT LIKE '%<inverse-' || CAST(wh.id AS TEXT) || '>%')

        )
        SELECT
            start_denom,
            id ,
            hops_len,
            target_denom,
            hops
        FROM cte;
            """)


def drop_view():
    engine.execute(drop_view_if_exist)


def create_or_alter_view():
    engine.execute(drop_view_if_exist)
    engine.execute(view_definition)
