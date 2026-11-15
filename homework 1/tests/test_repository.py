def test_repository_keeps_latest_result_for_each_item(repository):
    assert repository.get(10) is None

    repository.save(10, True)
    repository.save(20, False)
    repository.save(10, False)

    assert repository.get(10) is False
    assert repository.get(20) is False


def test_repository_instances_have_separate_storage(repository):
    other_repository = type(repository)()
    repository.save(10, True)

    assert other_repository.get(10) is None
