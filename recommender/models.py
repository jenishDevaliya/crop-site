from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
class Prediction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='predictions')
    N = models.FloatField()
    P = models.FloatField()
    k = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall =  models.FloatField()
    Predicted_label = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.Predicted_label}"
        
