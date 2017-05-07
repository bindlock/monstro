from monstro.utils.urls import include


patterns = []
patterns.extend(include('^', 'core.urls.patterns', namespace='core'))
