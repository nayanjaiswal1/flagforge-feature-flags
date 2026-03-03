from flagforge.storage.exceptions import StorageError


def test_storage_error():
    err = StorageError("message")
    assert str(err) == "message"
    assert isinstance(err, Exception)
