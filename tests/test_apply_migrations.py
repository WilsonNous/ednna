from ednna.infrastructure.apply_migrations import _statements


def test_sql_statement_splitter_ignores_empty_fragments():
    sql = """
    CREATE TABLE test_table (id INT);
    INSERT INTO test_table (id) VALUES (1);

    """

    assert _statements(sql) == (
        "CREATE TABLE test_table (id INT)",
        "INSERT INTO test_table (id) VALUES (1)",
    )
