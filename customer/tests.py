from django.test import TestCase
from django.contrib.auth.models import User

from .forms import SignUpForm


class SignUpFormTest(TestCase):

    def test_criar_customer_deve_criar_usuario(self):
        data = {'first_name': 'Rafael Reuber',
                'last_name': 'Bezerra Nogueira',
                'password1': 'qpp1p2o3po23',
                'password2': 'qpp1p2o3po23',
                'email': 'rafaelreuber@gmail.com'
                }
        form = SignUpForm(data)
        self.assertTrue(form.is_valid())
        form.save()

        user = User.objects.filter(username=data["email"]).first()
        self.assertIsNotNone(user)

    def test_nao_pode_criar_customer_com_email_test(self):
        data = {'first_name': 'Rafael Reuber',
                'last_name': 'Bezerra Nogueira',
                'password1': 'qpp1p2o3po23',
                'password2': 'qpp1p2o3po23',
                'email': 'rafaelreuber@test.com'
                }
        form = SignUpForm(data)
        self.assertFalse(form.is_valid())