-- create_tables.sql

-- Tabela: Clientes
CREATE TABLE Clientes (
    ID_Cliente INT AUTO_INCREMENT PRIMARY KEY,
    Nome_Cliente VARCHAR(255) NOT NULL,
    CNPJ VARCHAR(20),
    Contato VARCHAR(255)
);

-- Tabela: Players
CREATE TABLE Players (
    ID_Player INT AUTO_INCREMENT PRIMARY KEY,
    Nome_Player VARCHAR(255) NOT NULL,
    Tipo_Player ENUM('Banco', 'Adquirente', 'ERP', 'Outro') NOT NULL,
    Detalhes TEXT -- Ex.: Agência, Conta, Bandeira
);

-- Tabela: Operacoes
CREATE TABLE Operacoes (
    ID_Operacao INT AUTO_INCREMENT PRIMARY KEY,
    ID_Cliente INT NOT NULL, -- Referência ao cliente
    ID_Player INT NOT NULL, -- Referência ao player envolvido
    Tipo_Operacao ENUM('Abertura', 'Inclusão', 'Manutenção', 'Cancelamento') NOT NULL,
    Descricao_Problema TEXT,
    Status ENUM('Aberto', 'Em Processamento', 'Concluído', 'Cancelado') NOT NULL,
    Data_Cadastro DATE,
    FOREIGN KEY (ID_Cliente) REFERENCES Clientes(ID_Cliente),
    FOREIGN KEY (ID_Player) REFERENCES Players(ID_Player)
);

-- Tabela: Chamados_Redmine
CREATE TABLE Chamados_Redmine (
    ID_Chamado INT PRIMARY KEY, -- Identificador único do chamado no Redmine
    ID_Operacao INT NOT NULL, -- Referência à operação EDI associada
    Tipo_Problema VARCHAR(100), -- Ex.: Falta de Arquivo, Erro de Arquivo
    Estado VARCHAR(100), -- Ex.: Aberto, Aguardando Retorno
    Prioridade VARCHAR(50), -- Ex.: Normal, Alta, Urgente
    Assunto TEXT, -- Descrição resumida do problema
    Autor VARCHAR(255), -- Pessoa que criou o chamado
    Data_Inicio DATE,
    Data_Fim DATE,
    Data_Alterado DATETIME,
    Data_Criado DATETIME,
    Observacoes TEXT,
    FOREIGN KEY (ID_Operacao) REFERENCES Operacoes(ID_Operacao)
);

-- Tabela: Logs_Cancelamento
CREATE TABLE Logs_Cancelamento (
    ID_Log_Cancelamento INT AUTO_INCREMENT PRIMARY KEY,
    ID_Chamado INT NOT NULL, -- Referência ao chamado
    Player_Cancelado VARCHAR(255), -- Ex.: Cielo, Getnet
    Data_Cancelamento DATE,
    Observacoes TEXT,
    FOREIGN KEY (ID_Chamado) REFERENCES Chamados_Redmine(ID_Chamado)
);
