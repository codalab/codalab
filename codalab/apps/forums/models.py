import datetime

from django.core.urlresolvers import reverse
from django.db import models

from .helpers import send_mail


class Forum(models.Model):
    """
    Base Forum model.
    """
    competition = models.OneToOneField('web.Competition', unique=True, related_name="forum")

    @classmethod
    def competition_post_save(cls, **kwargs):
        competition = kwargs['instance']
        if not hasattr(competition, 'forum'):
            Forum.objects.create(competition=competition)


class Thread(models.Model):
    """
    Base Thread Model. Allows user to keep track of a new post.
    """
    forum = models.ForeignKey('forums.Forum', related_name="threads")
    date_created = models.DateTimeField()
    started_by = models.ForeignKey('authenz.ClUser')
    title = models.CharField(max_length=255)
    last_post_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-last_post_date',)

    def save(self, *args, **kwargs):
        created = False
        if not self.id:
            # On first save do these actions
            self.date_created = datetime.datetime.today()
            created = True

        # Do the save THEN send email so we have an Id to work with
        super(Thread, self).save(*args, **kwargs)

        if created:
            if self.forum.competition.creator.organizer_direct_message_updates:
                self.notify_user(self.forum.competition.creator)


    def get_absolute_url(self):
        return reverse('forum_thread_detail', kwargs={'forum_pk': self.forum.pk, 'thread_pk': self.pk})

    def notify_all_posters_of_new_post(self):
        """
        Notify users when a new post is created on the thread.
        """
        users_in_thread = set(post.posted_by for post in self.posts.all())

        for user in users_in_thread:
            self.notify_user(user)

    def notify_user(self, user):
        send_mail(
            context_data={
                'thread': self,
                'user': user,
            },
            subject='New post in %s' % self.title,
            html_file="forums/emails/new_post.html",
            text_file="forums/emails/new_post.txt",
            to_email=user.email
        )


class Post(models.Model):
    """
    Base Post model. Allows an authenticated user to post on a forum Thread.
    """
    thread = models.ForeignKey('forums.Thread', related_name="posts")
    date_created = models.DateTimeField()
    posted_by = models.ForeignKey('authenz.ClUser')
    content = models.TextField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_created = datetime.datetime.today()
        return super(Post, self).save(*args, **kwargs)
