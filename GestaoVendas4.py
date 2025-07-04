import flet as ft
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import webbrowser


class GestorVendasApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Gestão de Vendas"
        self.page.window_width = 600
        self.page.window_height = 700
        self.page.scroll = "auto"
        self.page.padding = 20
        self.page.bgcolor = "#f5f5f5"

        self.conectar_banco()
        self.criar_tabelas()
        self.usuario_logado = None

        self.carregar_login()

    def conectar_banco(self):
        self.conn = sqlite3.connect("database.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

    def criar_tabelas(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                preco REAL,
                quantidade INTEGER,
                data_venda TEXT
            )
        """)
        self.conn.commit()

    def carregar_login(self):
        self.page.controls.clear()

        self.usuario_input = ft.TextField(label="Usuário", width=300)
        self.senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)

        login_coluna = ft.Column(
            [
                ft.Text("Login de Usuário", size=28, weight="bold", color="#1976d2"),
                ft.Container(height=20),
                self.usuario_input,
                self.senha_input,
                ft.Row(
                    [
                        ft.ElevatedButton("Entrar", on_click=self.verificar_login, bgcolor="#1976d2", color="white"),
                        ft.TextButton("Criar Conta", on_click=self.criar_conta)
                    ],
                    alignment="center",
                    spacing=20
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )

        container_centralizado = ft.Container(
            content=login_coluna,
            width=360,
            height=300,
            alignment=ft.alignment.center,
            bgcolor="white",
            border_radius=10,
            padding=20,
            shadow=ft.BoxShadow(color="#aaa", blur_radius=10, offset=ft.Offset(0, 4)),
        )

        self.page.add(
            ft.Row(
                [container_centralizado],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                height=self.page.window_height,
            )
        )

        self.page.update()

    def verificar_login(self, e):
        usuario = self.usuario_input.value.strip()
        senha = self.senha_input.value.strip()

        if not usuario or not senha:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha usuário e senha!"), open=True)
            self.page.update()
            return

        self.cursor.execute("SELECT * FROM usuarios WHERE username=? AND senha=?", (usuario, senha))
        resultado = self.cursor.fetchone()

        if resultado:
            self.usuario_logado = usuario
            self.carregar_pagina_principal()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Login inválido!"), open=True)
            self.page.update()

    def criar_conta(self, e):
        usuario = self.usuario_input.value.strip()
        senha = self.senha_input.value.strip()

        if not usuario or not senha:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha usuário e senha!"), open=True)
            self.page.update()
            return

        try:
            self.cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (usuario, senha))
            self.conn.commit()
            self.page.snack_bar = ft.SnackBar(ft.Text("Conta criada com sucesso!"), open=True)
            self.page.update()
        except sqlite3.IntegrityError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Usuário já existe!"), open=True)
            self.page.update()

    def carregar_pagina_principal(self):
        self.page.controls.clear()

        self.page.appbar = ft.AppBar(
            title=ft.Text(f"Bem-vindo, {self.usuario_logado}", size=20),
            bgcolor="#1976d2",
            actions=[
                ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Sair", on_click=self.logout, icon_color="white")
            ]
        )

        self.tabs = ft.Tabs(
            selected_index=0,
            on_change=self.mudar_aba,
            tabs=[
                ft.Tab(text="Produtos"),
                ft.Tab(text="Vendas"),
                ft.Tab(text="Relatórios")
            ],
            indicator_color="#ff5722",
            label_color="#ff5722",
            unselected_label_color="#757575"
        )

        self.conteudo_aba = ft.Column(spacing=15, scroll="auto", expand=True)

        self.page.add(self.tabs, self.conteudo_aba)

        self.carregar_aba_produtos()

    def mudar_aba(self, e):
        if self.tabs.selected_index == 0:
            self.carregar_aba_produtos()
        elif self.tabs.selected_index == 1:
            self.carregar_aba_vendas()
        else:
            self.carregar_aba_relatorios()

    def carregar_aba_produtos(self):
        self.conteudo_aba.controls.clear()

        self.produto_nome = ft.TextField(label="Nome do Produto", width=300)
        self.produto_preco = ft.TextField(label="Preço (Kz)", keyboard_type="number", width=300)
        btn_cadastrar = ft.ElevatedButton("Cadastrar Produto", on_click=self.adicionar_produto, bgcolor="#1976d2",
                                          color="white")
        self.lista_produtos = ft.Column(spacing=8, expand=True)

        self.carregar_produtos()

        self.conteudo_aba.controls.extend([
            ft.Text("Cadastro de Produtos", size=22, weight="bold", color="#333"),
            self.produto_nome,
            self.produto_preco,
            btn_cadastrar,
            ft.Divider(thickness=1, color="#ddd"),
            ft.Text("Produtos Cadastrados:", size=20, weight="bold"),
            ft.Container(self.lista_produtos, height=300, bgcolor="white", padding=10, border_radius=5,
                         border=ft.border.all(1, "#ccc"))
        ])

        self.page.update()

    def adicionar_produto(self, e):
        nome = self.produto_nome.value.strip()
        preco = self.produto_preco.value.strip()

        if not nome or not preco:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), open=True)
            self.page.update()
            return

        try:
            preco = float(preco)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preço inválido!"), open=True)
            self.page.update()
            return

        self.cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
        self.conn.commit()

        self.produto_nome.value = ""
        self.produto_preco.value = ""

        self.carregar_produtos()

    def carregar_produtos(self):
        self.lista_produtos.controls.clear()
        self.cursor.execute("SELECT id, nome, preco FROM produtos ORDER BY nome")
        produtos = self.cursor.fetchall()

        for id, nome, preco in produtos:
            item = ft.ListTile(
                title=ft.Text(f"{nome} - {preco:.2f} Kz"),
                trailing=ft.IconButton(icon=ft.Icons.DELETE, tooltip="Remover",
                                       on_click=lambda e, pid=id: self.remover_produto(pid), icon_color="#d32f2f")
            )
            self.lista_produtos.controls.append(item)

        self.page.update()

    def remover_produto(self, produto_id):
        self.cursor.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        self.conn.commit()
        self.carregar_produtos()

    def carregar_aba_vendas(self):
        self.conteudo_aba.controls.clear()

        self.cursor.execute("SELECT id, nome, preco FROM produtos ORDER BY nome")
        produtos = self.cursor.fetchall()

        if not produtos:
            self.conteudo_aba.controls.append(ft.Text("Nenhum produto cadastrado ainda.", size=18, color="#999"))
            self.page.update()
            return

        options = [ft.dropdown.Option(f"{p[0]}|{p[1]}|{p[2]}") for p in produtos]

        self.produto_dropdown = ft.Dropdown(
            label="Produto",
            options=options,
            width=300,
            on_change=self.atualizar_preco
        )

        self.venda_preco = ft.TextField(label="Preço (Kz)", read_only=True, width=150)
        self.venda_quantidade = ft.TextField(label="Quantidade", value="1", keyboard_type="number", width=150)

        btn_registrar = ft.ElevatedButton("Registrar Venda", on_click=self.registrar_venda, bgcolor="#1976d2",
                                          color="white")

        self.conteudo_aba.controls.extend([
            ft.Text("Registrar Venda", size=22, weight="bold", color="#333"),
            self.produto_dropdown,
            ft.Row([self.venda_preco, self.venda_quantidade], spacing=20),
            btn_registrar
        ])

        self.page.update()

    def atualizar_preco(self, e):
        valor = self.produto_dropdown.value
        if valor:
            _, _, preco = valor.split("|")
            self.venda_preco.value = preco
            self.page.update()

    def registrar_venda(self, e):
        valor = self.produto_dropdown.value

        if not valor:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecione um produto!"), open=True)
            self.page.update()
            return

        produto_id, _, preco = valor.split("|")

        try:
            quantidade = int(self.venda_quantidade.value)
            if quantidade <= 0:
                raise ValueError()
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Quantidade inválida!"), open=True)
            self.page.update()
            return

        data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute(
            "INSERT INTO vendas (produto_id, preco, quantidade, data_venda) VALUES (?, ?, ?, ?)",
            (produto_id, float(preco), quantidade, data_venda)
        )
        self.conn.commit()

        self.page.snack_bar = ft.SnackBar(ft.Text("Venda registrada!"), open=True)
        self.carregar_aba_vendas()

    def carregar_aba_relatorios(self):
        self.conteudo_aba.controls.clear()

        self.cursor.execute("""
            SELECT v.id, p.nome, v.preco, v.quantidade, v.data_venda 
            FROM vendas v 
            JOIN produtos p ON v.produto_id = p.id 
            ORDER BY v.data_venda DESC
        """)

        vendas = self.cursor.fetchall()
        lista_vendas = ft.Column(spacing=6, expand=True)
        total_geral = 0

        for _, nome, preco, quantidade, data in vendas:
            subtotal = preco * quantidade
            total_geral += subtotal
            lista_vendas.controls.append(
                ft.Text(f"{data} | {nome} | {quantidade} un. | {preco:.2f} Kz | Subtotal: {subtotal:.2f} Kz", size=14)
            )

        if not vendas:
            lista_vendas.controls.append(ft.Text("Nenhuma venda registrada.", size=16, color="#999"))

        lista_vendas.controls.append(ft.Divider(thickness=1, color="#ccc"))
        lista_vendas.controls.append(
            ft.Text(f"Total geral: {total_geral:.2f} Kz", weight="bold", size=16)
        )

        btn_pdf = ft.ElevatedButton("📄 Gerar PDF", on_click=self.gerar_pdf_relatorio, bgcolor="#1976d2", color="white")

        self.conteudo_aba.controls.extend([
            ft.Text("Relatório de Vendas", size=22, weight="bold", color="#333"),
            ft.Container(lista_vendas, height=350, bgcolor="white", padding=15, border_radius=5,
                         border=ft.border.all(1, "#ccc")),
            btn_pdf
        ])

        self.page.update()

    def gerar_pdf_relatorio(self, e):
        self.cursor.execute("""
            SELECT v.id, p.nome, v.preco, v.quantidade, v.data_venda 
            FROM vendas v 
            JOIN produtos p ON v.produto_id = p.id 
            ORDER BY v.data_venda DESC
        """)

        vendas = self.cursor.fetchall()

        if not vendas:
            self.page.snack_bar = ft.SnackBar(ft.Text("Nenhuma venda para gerar PDF!"), open=True)
            self.page.update()
            return

        pdf_file = f"relatorio_vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4

        def cabecalho(y):
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, "📑 Relatório de Vendas")
            c.setFont("Helvetica", 12)
            c.drawString(50, y - 20, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            y -= 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Data")
            c.drawString(150, y, "Produto")
            c.drawRightString(300, y, "Qtd")
            c.drawRightString(370, y, "Preço (Kz)")
            c.drawRightString(460, y, "Subtotal")
            return y - 20

        y = height - 50
        y = cabecalho(y)
        total_geral = 0
        c.setFont("Helvetica", 11)

        for _, nome, preco, quantidade, data in vendas:
            if y < 60:
                c.showPage()
                y = height - 50
                y = cabecalho(y)
                c.setFont("Helvetica", 11)
            subtotal = preco * quantidade
            total_geral += subtotal
            c.drawString(40, y, data)
            c.drawString(150, y, nome)
            c.drawRightString(300, y, str(quantidade))
            c.drawRightString(370, y, f"{preco:.2f}")
            c.drawRightString(460, y, f"{subtotal:.2f}")
            y -= 22

        c.setFont("Helvetica-Bold", 12)
        if y < 60:
            c.showPage()
            y = height - 50
            y = cabecalho(y)
        c.drawString(40, y - 20, f"Total Geral: {total_geral:.2f} Kz")
        c.save()

        local_absoluto = os.path.abspath(pdf_file)
        self.page.snack_bar = ft.SnackBar(ft.Text(f"PDF salvo em: {local_absoluto}"), open=True)
        self.page.update()

        try:
            webbrowser.open(f"file://{local_absoluto}")
        except:
            pass

    def logout(self, e):
        self.usuario_logado = None
        self.page.appbar = None
        self.carregar_login()


def main(page: ft.Page):
    GestorVendasApp(page)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0))
    if port == 0:
        ft.app(target=main, view=ft.WEB_BROWSER, port=5000)
    else:
        ft.app(target=main, port=port)
