def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that require a live Postgres + Gold layer",
    )
