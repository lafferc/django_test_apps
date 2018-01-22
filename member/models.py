from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    display_name_format = models.IntegerField(
            default=0,
            choices=((0, "Full Name"),
                     (1, "username"),
                     (2, "user_id")))
    can_receive_emails = models.BooleanField(
            default=True,
            help_text="Global email setting, if false the user will not receive any emails")
    email_on_new_competition = models.BooleanField(
            default=True,
            help_text="User will receive an email when new competitions are started")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
