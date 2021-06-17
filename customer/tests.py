from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .forms import SignUpForm


class SignUpFormTest(TestCase):

    def test_criar_customer_deve_criar_usuario(self):
        data = {'first_name': 'Rafael Reuber',
                'last_name': 'Bezerra Nogueira',
                'password1': 'qpp1p2o3po23',
                'password2': 'qpp1p2o3po23',
                'email': 'rafaelreuber@gmail.com',
                'address': 'Rua A',
                'city': 'Iracema',
                'zip': '62000',
                'cellphone': '9855445123',
                'terms_confirmed': True
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

    def test_save_deve_falhar_se_dados_forem_invalidos(self):
        data = {'first_name': 'Rafael Reuber',
                'last_name': 'Bezerra Nogueira',
                'password1': 'qpp1p2o3po23',
                'password2': 'qpp1p2o3po23',
                'email': 'rafaelreuber@test.com'
                }
        form = SignUpForm(data)
        with self.assertRaises(ValidationError) as err:
            form.save()
