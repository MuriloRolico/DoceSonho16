from flask import Blueprint, render_template

# Criar blueprint para a página sobre nós
sobrenos_bp = Blueprint('sobrenos', __name__)

@sobrenos_bp.route('/sobre-nos')
def sobrenos():
    return render_template('sobrenos.html')