<!--
   /* cSpell:locale en pt-br
   /* cSpell:ignore sendgrid sqlalchemy
   /* mgd 2024-05-03, 07-30
-->
# — Canoa _Frontend_ de AdaptaBrasil —


## Processo de Validação

A validação do arquivo ```zip``` é realizado por um aplicativo externo, o
    [```Validador```](https://github.com/AdaptaBrasil/data_validate),
    e gerenciado por ```.private.upload_file.process.py```
    que consta dos seguintes módulos:


> Ao lado do nome da unidade é mostrado [módulo python e o Código Base de Erro (```CBE```), ver ```.helpers.error_helper.py```]


1. ### _Admit_ [```receive_file.py```, ```CBE```:```200```] ###
   #### Recebe arquivo ou link do usuário ####
    - Cria o formulário para o usuário informar:
        + Nome do arquivo
        + _ou_
        + Link a um arquivo em _Google Drive_
    - Valida que seja enviado somente um dado
    - Se enviou um link _(download)_
        + Valida o link
        + Faz _download_ do arquivo na pasta apropriada (ver estrutura de pastas)
    - Se enviou um arquivo  _(upload)_
        + Valida o nome, tamanho
        + Revisa o tipo de conteúdo (que é salvo localmente durante o registro)
    - Inicia o process


2. ### _Process_ [```process.py```, ```CBE```:```270```] ###
    #### Gerencia o processo ####
    - Chama os módulos sequencialmente:
       + Revisar
       + Registrar no DB
       + Descompactar
       + Submeter a validação
       + Enviar resultado
    - Cuida dos parâmetros e retornos entre eles
    - Supervisiona o andamento de cada passo
    - Em caso de erro:
        + Se o processo ja foi registrado, grava a mensagens, códigos, exceções e módulo ativo
        + Abandona a iteração
        + Informa ao usuário
        + Fecha o registro do processo, anotando as mensagens de erro
    - Em caso de sucesso:
        + Fecha o registro do processo, anotando as mensagens recebidas
    - Atualiza o formulário do usuário com o resultado
    - Se ocorrer excepção durante a execução de um módulos, é somado
       ```RECEIVE_FILE_EXCEPTION``` 100 ao
       código de erro.
       Assim, os possíveis códigos de erro são:
       ```RECEIVE_FILE_*``` => [200...270] + 100

3. ### _Check_  [```check.py```, ```CBE```:```210```] ###
    #### Revisa os requisitos do processo ####
    - Corrobora a presencia das configurações:
        + ```config.py``` configuração geral
        + ```config_upload.py``` especifica do processo
    - Revisa as variáveis e o arquivos necessários
    - Examina a existência das pastas e as criar caso não existam
    - Valida o nome, tamanho e extensão do arquivo
    - Verifica a disponibilidade dos _scripts_ de execução do ```Validator``` e se eles estão atualizados
    - Confirma se os dados do usuário estão completos, incluindo e-mail

4. ### _Register_ [```register.py```, ```CBE```:```230```] ###
    #### Registra o processo  ####
    - Cria o ticket (chave única) e o número de protocolo do processo
    - Se enviou um arquivo  _(upload)_, salva o conteúdo localmente.
    - Coleta informações do arquivo como ```crc32``` e tamanho
    - Insere registro na tabela (```user_data_files```) com os dados do
      usuário e do arquivo submetido

5. ### _Unzip_ [```unzip.py```, ```CBE```:```240```] ###
    #### Descompacta o arquivo  ####
    - Valida se é o arquivo está no formato ```zip```
    - Extrai o conteúdo na pasta do usuário que e compartilhada com
      o aplicativo validador.

6. ### _Submit_  [```submit.py```, ```CBE```:```250```] ###
    #### Chama ao aplicativo validador  ####

7. ### _E-Mail_  [```mail.py```, ```CBE```:```260```] ###
    #### Envia o email de resultado  ####


## Estrutura de Pastas ##

    [Projeto]
    │
    ├── data_validate
    │    ├── main.py           > inicia a validação
    │    │
    :    :

    :
    ├── canoa
    :    ├── main.py           > prepara e inicia o App
         ├── carranca          > a pasta principal do App
         │    ├── shared.py      » variáveis compartilhadas
         │    └── ...
         ├── user_files        > contem os arquivos dos usuários
         │    ├── downloaded     » baixados da nuvem
         │    │    ├── cod_1        · do usuário 1
         │    │    ├── cod_2        · do usuário 2
         │    │    :
         │    │    └── cod_N        · do usuário n
         │    └── uploaded       » subidos da maquina do usuário
         │    │    ├── cod_1        · do usuário 1
         │    │    ├── cod_2        · do usuário 2
         │    │    :
         │    │    └── cod_N        · do usuário n




## Variáveis de Ambiente

Para manter a privacidade e a segurança das informações confidenciais, são usadas
variáveis de ambiente (`envvars` [_Environment Variables_](https://en.wikipedia.org/wiki/Environment_variable)). As principais são:

- `CANOA_APP_MODE` seleciona o modo da aplicação, selecionando configurações diferentes. Atualmente temos `Production` e `Debug`.
  Para maiores detalhes e novas configurações ver o módulo `./config.py`.
- `CANOA_DEBUG` configura o modo da aplicação: `False` ou `True`. Para ativar o modo depuração em Flask, deve usar
    [`FLASK_DEBUG`](https://flask.palletsprojects.com/en/latest/config/#DEBUG);
- `CANOA_EMAIL_API_KEY` A chave da API para o envio de e-mails (o app usa [sendgrid](https://sendgrid.com/));
- `CANOA_EMAIL_ORIGINATOR` O endereço de e-mail do remetente, quem envia correios em nome de Canoa e está registrado na API de envio;
- `CANOA_SQLALCHEMY_DATABASE_URI` O URI do banco de dados que deve ser usado para a conexão usando
    [Flask&minus;SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/latest/config);

Qualquer atributo da configuração base (`BaseConfig` em  `.config.py`) pode ser configurado por meio de uma envvar.
Basta adicionar o nome do atributo antecedido com CANOA na lista (ver ```.config.get_os_env```)

É possível atribuir um valor fixo para a envvar [`SECRET_KEY`](https://flask.palletsprojects.com/en/latest/config/#SECRET_KEY),
mas se é deixado em branco, o sistema gerara um nova valor a cada variação da versão do aplicativo.




