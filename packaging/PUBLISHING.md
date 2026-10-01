# Publier une release

Deux cibles : **PyPI** (`pipx install phone-mirror`) puis **AUR** (`phone-mirror`), qui
consomme le sdist PyPI. Les deux sont automatisées par `.github/workflows/release.yml`
au push d'un tag `v*`, comme pour wpe-manager.

## 0. Mise en place (une seule fois)

1. **GitHub** : créer le dépôt `Dragonir44/phone-mirror`, puis :
   ```bash
   git remote add origin https://github.com/Dragonir44/phone-mirror.git
   git push -u origin main
   ```
2. **PyPI — trusted publishing** (pas de jeton à stocker) : sur https://pypi.org →
   *Your projects* → *Publishing* → *Add a new pending publisher* :
   - PyPI project name : `phone-mirror`
   - Owner : `Dragonir44`, repository : `phone-mirror`
   - Workflow : `release.yml`, environment : laisser vide
3. **AUR** : le paquet est créé au premier push. Ajouter la clé SSH privée du compte AUR
   dans les secrets du dépôt GitHub sous le nom `AUR_SSH_PRIVATE_KEY` (même clé que pour
   wpe-manager).

## 1. Release

La version vit **uniquement** dans `phone_mirror/__init__.py` (`__version__`) ;
`pyproject.toml` la lit dynamiquement.

1. Mettre à jour `__version__`.
2. Committer, puis taguer et pousser :
   ```bash
   git tag v0.1.0 && git push && git push --tags
   ```

Le workflow vérifie que le tag correspond à `__version__`, lance les tests (catalogue de
traduction complet), publie sur PyPI, puis met `pkgver` + `sha256sums` du `PKGBUILD` à
jour depuis le sdist publié et pousse sur l'AUR.

## Tester avant de publier

```bash
python -m pytest -q tests          # traductions
python -m build                    # dist/*.tar.gz + *.whl
cd packaging/aur && makepkg -si    # après publication PyPI (le PKGBUILD télécharge le sdist)
```

## Traductions

Les textes de l'interface sont en anglais dans le code, passés à `_()`. Le français est
dans `phone_mirror/locales/fr.py` (clé = texte anglais exact). Après avoir ajouté ou
modifié un texte, compléter le catalogue : `tests/test_i18n.py` échoue tant qu'il manque
une traduction ou que les `{variables}` diffèrent.
