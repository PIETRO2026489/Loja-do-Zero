# Loja-do-Zero
Jogo feito por Pietro, apenas por diversão
Loja do Zero

Um jogo 2D casual de gerenciamento de loja feito em Python + Pygame, com visual original e arquitetura preparada para rodar tanto no desktop quanto no navegador usando pygbag/WebAssembly.

O que já existe

Loja em visão 2D com expansão visual por nível.

Fluxo de comprar estoque -> abastecer prateleiras -> atender clientes -> vender -> reinvestir.

10 produtos com desbloqueio progressivo.

5 níveis de loja: Mercadinho, Loja de Bairro, Supermercado, Mega Loja e Loja Premium.

6 categorias de melhoria.

3 tipos de funcionários.

Clientes com perfis diferentes e comportamento simples.

Satisfação da clientela.

Missões e conquistas.

Eventos temporários: promoção, movimento intenso e oferta do fornecedor.

Salários dos funcionários.

Salvamento automático.

Salvamento em localStorage quando o jogo está no navegador via pygbag; arquivo JSON quando executado no desktop.

Layout responsivo por escala para diferentes tamanhos de janela.

Nenhum asset externo obrigatório: os elementos gráficos principais são desenhados via Pygame.

Estrutura

loja_do_zero/
├── main.py
├── README.md
├── requirements.txt
└── .github/
    └── workflows/
        └── build.yml

Rodar no computador

Recomendado: Python 3.11+.

python -m venv .venv

Windows:

.venv\Scripts\activate

Linux/macOS:

source .venv/bin/activate

Instale as dependências:

pip install -r requirements.txt

Execute:

python main.py

Controles

Mouse: navegar pelos menus e clicar nas ações.

F5: salvar manualmente.

F2: começar uma nova partida.

Esc: sair.

Como jogar

No início, compre cinco unidades de um produto.

Vá para ESTOQUE e coloque parte do estoque na prateleira.

Volte para LOJA e espere os clientes entrarem.

O cliente procura um item disponível, compra e vai ao caixa.

Use o faturamento para ampliar prateleiras, espaço, estoque, iluminação, limpeza e entrada.

No nível 2, contrate funcionários.

Aumente o faturamento para liberar novos produtos e novas áreas.

Progressão

Nível

Nome

Faturamento acumulado para chegar ao nível

1

Mercadinho

R$ 0

2

Loja de Bairro

R$ 250

3

Supermercado

R$ 900

4

Mega Loja

R$ 2.200

5

Loja Premium

R$ 5.000

Produtos

Os três primeiros produtos estão liberados desde o início:

Maçã

Pão

Leite

Depois são liberados progressivamente:

Chocolate

Refrigerante

Pizza

Fone

Videogame

Celular

Computador

Geração da versão web

O projeto está preparado para pygbag. Em ambiente local, instale:

pip install pygbag

Gere a versão web com:

pygbag main.py

O comando cria a pasta de distribuição web. Para testar localmente, use o servidor HTTP indicado pelo próprio pygbag ou o fluxo de desenvolvimento documentado pela versão instalada.

GitHub Actions

O workflow em .github/workflows/build.yml instala as dependências e executa o build do pygbag a cada push. O artefato gerado é disponibilizado como artefato do workflow.

Observações técnicas

Salvamento

No desktop, o jogo utiliza loja_do_zero_save.json. O arquivo é escrito de forma segura usando um arquivo temporário e os.replace.

No navegador, o código tenta usar window.localStorage por meio do módulo js, disponível no ambiente pygbag. Existe fallback para o modo desktop.

Compatibilidade

A lógica usa uma resolução lógica fixa de 1280x720 e desenha a tela final em escala proporcional para se adaptar a janelas menores ou maiores.

Próximas extensões possíveis

sistema de layout manual das prateleiras;

mapa com múltiplas salas;

sistema financeiro diário mais profundo;

personalização visual da loja;

mais tipos de clientes;

sistema de reputação;

sons e música originais;

modo de dificuldade;

telas de pausa e configurações;

tutorial contextual em vez de tutorial inicial único.

Licença

Código do protótipo disponibilizado para estudo e evolução do projeto. Os elementos visuais são gerados pelo próprio código e não dependem de assets protegidos de terceiros.
