import typer 
from .startgame import startgame


app = typer.Typer()
app.command()(startgame)


if __name__ == '__main__':
    app()
