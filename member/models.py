from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
import smtplib

g_logger = logging.getLogger(__name__)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    display_name_format = models.IntegerField(
            default=0,
            choices=((0, "Full Name"),
                     (1, "username"),
                     (2, "user_id")),
            help_text="This how other users will see you name displayed")
    can_receive_emails = models.BooleanField(
            default=True,
            help_text="Global email setting, if false the user will not receive any emails")
    email_on_new_competition = models.BooleanField(
            default=True,
            help_text="User will receive an email when new competitions are started")
    
    def get_name(self):
        if self.display_name_format == 0:
            name = "%s %s" % (self.user.first_name, self.user.last_name)
            if name == " ":
                name = self.user.username
            return name
        if self.display_name_format == 1:
            return "%s" % self.user.username
        if self.display_name_format == 2:
            return "user_%d" % self.user.pk

    def email_user(self, subject, message, new_comp=False):
        if not self.can_receive_emails:
            return
        if new_comp and not self.email_on_new_competition:
            return
        try:
            self.user.email_user(subject, message)
        except smtplib.SMTPRecipientsRefused:
            g_logger.error("Recipient Refused:'%s' (user: %s)", 
                           self.user.email, self.user)
    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
