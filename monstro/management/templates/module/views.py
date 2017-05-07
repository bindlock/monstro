import monstro.views


class IndexView(monstro.views.View):

    def get(self):
        self.write('Hello from Monstro!')
