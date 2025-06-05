CREATE DATABASE IF NOT EXISTS dudulist;
USE dudulist;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(220) UNIQUE NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    email VARCHAR(220) UNIQUE NOT NULL,
    password VARCHAR(220) NOT NULL,
    fdn DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE prioridades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE estados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE tareas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    categoria_id INT NOT NULL,
    prioridad_id INT NOT NULL,
    estado_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_limite DATETIME,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visible BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (prioridad_id) REFERENCES prioridades(id),
    FOREIGN KEY (estado_id) REFERENCES estados(id)
) ENGINE=InnoDB;

INSERT INTO categorias (nombre) VALUES 
('Personal'),
('Trabajo'),
('Estudio'),
('Hogar'),
('Finanzas'),
('Salud'),
('Compras'),
('Proyectos'),
('Reuniones');

INSERT INTO prioridades (nombre) VALUES 
('Alta'),
('Media'),
('Baja');

INSERT INTO estados (nombre) VALUES 
('Pendiente'),
('En progreso'),
('Completada'),
('Cancelada');