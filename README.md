# EDNNA — Netunna

A EDNNA está evoluindo de um chatbot monolítico para a camada de orquestração das
inteligências especializadas da Netunna.

## Princípio arquitetural

- **EDNNA orquestra.**
- **Especialistas dominam seus próprios domínios.**
- Especialistas expõem **capabilities** por contratos; a EDNNA não acessa seus bancos internos.
- Consultas e ações devem permanecer separadas, autenticadas, autorizadas e auditáveis.

O EDDY é o primeiro especialista registrado e representa o domínio de EDI.

## Fundação atual

A fundação inicial inclui:

- contratos tipados de capabilities;
- registro de especialistas;
- roteamento por capability;
- descriptor inicial do EDDY;
- testes automatizados;
- pipeline único de validação e deploy no Azure.

A integração de rede com o EDDY ainda não está habilitada nesta fase.

## Configuração local

Copie `.env.example` para `.env` e preencha os valores reais localmente.
Nunca versione credenciais ou segredos.

Variáveis obrigatórias:

- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

`DB_PORT` é opcional e usa `3306` por padrão.

## Segurança

Credenciais anteriormente versionadas devem ser consideradas comprometidas e precisam ser
rotacionadas antes da promoção desta branch para produção.
