# Eventlinez

<!---Esses são exemplos. Veja https://shields.io para outras pessoas ou para personalizar este conjunto de escudos. Você pode querer incluir dependências, status do projeto e informações de licença aqui--->


<img src="exemplo-image.png" alt="exemplo imagem">

> EventLinez tem o objetivo de ajudar os promotores de eventos, proprietários de bares, proprietários de locais e buscadores de entretenimento a capturar o público certo.

## 💻 Pré-requisitos

São necessárias algumas configurações no <nome-do-projeto> , como:

| Variável         | Descrição                                                     | Valor Padrão |
| ---------------- | ------------------------------------------------------------- | ------------ |
| EVENTLINEZ_FEE   | Taxa de cobraça do eventlinez                                 |              |
| APP_HOST         | URL base do sistema                                           |              |
| STATIC_ROOT      | Diretório onde serão replicados os arquivos estáticos         | /static      |
| DEBUG            | Faz com que o Django execute em modo Debug                    | False        |
| SECRET_KEY       | Configura chave de segurança do Django                        |              |
| ALLOWED_HOSTS    | Restringe os HOSTs que irão acessar a aplicação               | 127.0.0.1    | 
| SENTRY_DSN       | Chave configuração de integração com a Sentry                 |              |
| MEDIA_ROOT       | Local onde os arquivos de média serão armazenados             |              |
| STRIPE_PUBLISHABLE_KEY | Chave do stripe                                         |              |
| STRIPE_SECRET_KEY| Chave do stripe                                               |              |

## 🚀 Instalando <eventlinez>

##### Criar uma virtual environment com virtualenv:

```pip install virtualenv```

```virtualenv nome_da_virtualenv```

Aivar virtual environment:

```source nome_da_virtualenv/bin/activate ```

Instalando Dependencias 

```pip install -r requirements.txt```

Migrate:

```python manage.py makemigrations```
e
```python manage.py migrate```


## ☕ Usando <nome-do-projeto>

Para usar <nome-do-projeto>, basta rodar o servidor:

 ```
 python manage.py runserver
 ```

### Novas funcionalidades 

As próximas atualizações serão voltadas nas seguintes funcionalidades:

- [x] Gerar QR-CODE
- [x] Gerar PDF do ingresso
- [x] Check-in dos ingressos

## 📫 Contribuindo para <nome_do_projeto>

1. Bifurque este repositório.
2. Crie um branch: `git checkout -b <nome_branch>`.
3. Faça suas alterações e confirme-as: `git commit -m '<mensagem_commit>'`
4. Envie para o branch original: `git push origin <nome_do_projeto> / <local>`
5. Crie a solicitação de pull.

Como alternativa, consulte a documentação do GitHub em [como criar uma solicitação pull](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

## 🤝 Colaboradores

As seguintes pessoas que contribuem para este projeto:

<table>
  <tr>
    <td align="center">
      <a href="#">
        <img src="https://avatars3.githubusercontent.com/u/127780" width="100px;" alt="Foto do Iuri Silva no GitHub"/><br>
        <sub>
          <b>Rafael Reuber</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="#">
        <img src="https://s2.glbimg.com/FUcw2usZfSTL6yCCGj3L3v3SpJ8=/smart/e.glbimg.com/og/ed/f/original/2019/04/25/zuckerberg_podcast.jpg" width="100px;" alt="Foto do Mark Zuckerberg"/><br>
        <sub>
          <b>Bruno José</b>
        </sub>
      </a>
    </td>
  </tr>
</table>


## 📝 Licença

Esse projeto está sob licença. Veja o arquivo [LICENÇA](LICENSE.md) para mais detalhes.

[⬆ Voltar ao topo](#nome-do-projeto)<br>


