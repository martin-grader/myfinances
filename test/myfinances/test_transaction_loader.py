from myfinances.transaction_loader import TransactionLoader


def test_transaction_loader() -> None:
    loader: TransactionLoader = TransactionLoader()
    assert loader.df.empty
