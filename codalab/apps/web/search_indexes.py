from haystack import indexes
from .models import Competition

class CompetitionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    end_date = indexes.DateTimeField(model_attr='end_date')
    creator = indexes.CharField(model_attr='creator')
    modified_by = indexes.CharField(model_attr='modified_by')
    last_modified = indexes.DateTimeField(model_attr='last_modified')
    published = indexes.BooleanField(model_attr='published')

    def get_model(self):
        return Competition

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(published=True)