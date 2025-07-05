
-- SQL para criar usuário admin
USE doce_sonho;

-- Remover admin existente (se houver)
DELETE FROM usuario WHERE email = 'admin@gmail.com';

-- Criar novo admin
INSERT INTO usuario (nome, email, senha, is_admin, concordou_politica, status) 
VALUES ('Murilo', 'admin@gmail.com', 'scrypt:32768:8:1$J12fOLrZFIKUrIEN$368ae07e9f89bfedd8f8c1a3fff54bb65b76a199e964efe58efea71e5f2663bb6aaad5eaf5813412e9c801f8c1a5f52f1c0e41705d93b2f4ac017e6c05d3ad05', TRUE, TRUE, 'ativo');

-- Verificar se foi criado
SELECT id, nome, email, is_admin, status FROM usuario WHERE email = 'admin@gmail.com';
