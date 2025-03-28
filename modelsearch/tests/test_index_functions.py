from datetime import date
from unittest import mock

from django.test import TestCase, override_settings

from modelsearch import index
from modelsearch.test.testapp import models
from modelsearch.test.utils import ModelSearchTestCase


class TestGetIndexedInstance(TestCase):
    fixtures = ["search"]

    def test_gets_instance(self):
        obj = models.Author.objects.get(id=1)

        # Should just return the object
        indexed_instance = index.get_indexed_instance(obj)
        self.assertEqual(indexed_instance, obj)

    def test_gets_specific_class(self):
        obj = models.Novel.objects.get(id=1)

        # Running the command with the parent class should find the specific class again
        indexed_instance = index.get_indexed_instance(obj.book_ptr)
        self.assertEqual(indexed_instance, obj)

    def test_blocks_not_in_indexed_objects(self):
        obj = models.Novel(
            title="Don't index me!",
            publication_date=date(2017, 10, 18),
            number_of_pages=100,
        )
        obj.save()

        # We've told it not to index anything with the title "Don't index me"
        # get_indexed_instance should return None
        indexed_instance = index.get_indexed_instance(obj.book_ptr)
        self.assertIsNone(indexed_instance)


@mock.patch("modelsearch.tests.DummySearchBackend", create=True)
@override_settings(
    MODELSEARCH_BACKENDS={
        "default": {"BACKEND": "modelsearch.tests.DummySearchBackend"}
    }
)
class TestInsertOrUpdateObject(ModelSearchTestCase):
    def test_inserts_object(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )
        backend().reset_mock()

        index.insert_or_update_object(obj)

        backend().add.assert_called_with(obj)

    def test_doesnt_insert_unsaved_object(self, backend):
        obj = models.Book(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )
        backend().reset_mock()

        index.insert_or_update_object(obj)

        self.assertFalse(backend().add.mock_calls)

    # TODO: Replace with non-Wagtail model
    # def test_converts_to_specific_page(self, backend):
    #     root_page = Page.objects.get(id=1)
    #     page = root_page.add_child(
    #         instance=SimplePage(title="test", slug="test", content="test")
    #     )

    #     # Convert page into a generic "Page" object and add it into the index
    #     unspecific_page = page.page_ptr

    #     backend().reset_mock()

    #     index.insert_or_update_object(unspecific_page)

    #     # It should be automatically converted back to the specific version
    #     backend().add.assert_called_with(page)

    def test_catches_index_error(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )

        backend().add.side_effect = ValueError("Test")
        backend().reset_mock()

        with self.assertLogs("modelsearch.index", level="ERROR") as cm:
            index.insert_or_update_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn(
            "Exception raised while adding <Book: Test> into the 'default' search backend",
            cm.output[0],
        )
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])


@mock.patch("modelsearch.tests.DummySearchBackend", create=True)
@override_settings(
    MODELSEARCH_BACKENDS={
        "default": {"BACKEND": "modelsearch.tests.DummySearchBackend"}
    }
)
class TestRemoveObject(ModelSearchTestCase):
    def test_removes_object(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )
        backend().reset_mock()

        index.remove_object(obj)

        backend().delete.assert_called_with(obj)

    def test_removes_unsaved_object(self, backend):
        obj = models.Book(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )
        backend().reset_mock()

        index.remove_object(obj)

        backend().delete.assert_called_with(obj)

    def test_catches_index_error(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )
        backend().reset_mock()

        backend().delete.side_effect = ValueError("Test")

        with self.assertLogs("modelsearch.index", level="ERROR") as cm:
            index.remove_object(obj)

        self.assertEqual(len(cm.output), 1)
        self.assertIn(
            "Exception raised while deleting <Book: Test> from the 'default' search backend",
            cm.output[0],
        )
        self.assertIn("Traceback (most recent call last):", cm.output[0])
        self.assertIn("ValueError: Test", cm.output[0])


@mock.patch("modelsearch.tests.DummySearchBackend", create=True)
@override_settings(
    MODELSEARCH_BACKENDS={
        "default": {"BACKEND": "modelsearch.tests.DummySearchBackend"}
    }
)
class TestSignalHandlers(ModelSearchTestCase):
    def test_index_on_create(self, backend):
        backend().reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            obj = models.Book.objects.create(
                title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
            )
        backend().add.assert_called_with(obj)

    # TODO: Replace with non-Wagtail model
    # def test_index_on_create_with_uuid_primary_key(self, backend):
    #     backend().reset_mock()
    #     with self.captureOnCommitCallbacks(execute=True):
    #         obj = AdvertWithCustomUUIDPrimaryKey.objects.create(text="Test")
    #     backend().add.assert_called_with(obj)

    def test_index_on_update(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )

        backend().reset_mock()
        obj.title = "Updated test"
        with self.captureOnCommitCallbacks(execute=True):
            obj.save()

        self.assertEqual(backend().add.call_count, 1)
        indexed_object = backend().add.call_args[0][0]
        self.assertEqual(indexed_object.title, "Updated test")

    # TODO: Replace with non-Wagtail model
    # def test_index_on_update_with_uuid_primary_key(self, backend):
    #     obj = AdvertWithCustomUUIDPrimaryKey.objects.create(text="Test")

    #     backend().reset_mock()
    #     obj.text = "Updated test"
    #     with self.captureOnCommitCallbacks(execute=True):
    #         obj.save()

    #     self.assertEqual(backend().add.call_count, 1)
    #     indexed_object = backend().add.call_args[0][0]
    #     self.assertEqual(indexed_object.text, "Updated test")

    def test_index_on_delete(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )

        backend().reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            obj.delete()
        backend().delete.assert_called_with(obj)

    # TODO: Replace with non-Wagtail model
    # def test_index_on_delete_with_uuid_primary_key(self, backend):
    #     obj = AdvertWithCustomUUIDPrimaryKey.objects.create(text="Test")

    #     backend().reset_mock()
    #     with self.captureOnCommitCallbacks(execute=True):
    #         obj.delete()
    #     backend().delete.assert_called_with(obj)

    def test_do_not_index_fields_omitted_from_update_fields(self, backend):
        obj = models.Book.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )

        backend().reset_mock()
        obj.title = "Updated test"
        obj.publication_date = date(2001, 10, 19)
        with self.captureOnCommitCallbacks(execute=True):
            obj.save(update_fields=["title"])

        self.assertEqual(backend().add.call_count, 1)
        indexed_object = backend().add.call_args[0][0]
        self.assertEqual(indexed_object.title, "Updated test")
        self.assertEqual(indexed_object.publication_date, date(2017, 10, 18))


@mock.patch("modelsearch.tests.DummySearchBackend", create=True)
@override_settings(
    MODELSEARCH_BACKENDS={
        "default": {"BACKEND": "modelsearch.tests.DummySearchBackend"}
    }
)
class TestSignalHandlersSearchDisabled(ModelSearchTestCase):
    def test_index_on_create_and_update(self, backend):
        obj = models.UnindexedBook.objects.create(
            title="Test", publication_date=date(2017, 10, 18), number_of_pages=100
        )

        self.assertEqual(backend().add.call_count, 0)
        self.assertIsNone(backend().add.call_args)

        backend().reset_mock()
        obj.title = "Updated test"
        obj.save()

        self.assertEqual(backend().add.call_count, 0)
        self.assertIsNone(backend().add.call_args)
