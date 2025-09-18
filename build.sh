#!/bin/bash
# Script de build para o Render

echo "Instalando dependências Python..."
pip install -r requirements.txt

echo "Configurando permissões..."
chmod a+x app.py

echo "Build completo!"
