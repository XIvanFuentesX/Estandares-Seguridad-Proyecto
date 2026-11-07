CREATE TABLE IF NOT EXISTS cursos (
  codigo varchar(20) PRIMARY KEY,
  nombre varchar(120) NOT NULL
);
INSERT INTO cursos (codigo, nombre) VALUES
 ('SEG-101','Fundamentos de Ciberseguridad'),
 ('RED-201','Redes Seguras'),
 ('SGSI-301','Gestion de Seguridad de la Informacion')
ON CONFLICT DO NOTHING;
