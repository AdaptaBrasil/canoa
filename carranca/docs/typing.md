### Convenções de Nomenclatura em Canoa

| Elemento | Convenção | Exemplo |
| :--- | :--- | :--- |
| *Canoa* **Type Alias** | `Snake_case` | `Db_texts`  |
| **Type Alias** |  `snake_case` | `db_texts`  |
| **Classe** | `PascalCase` | `UiDbTexts` |
| **Variável** | `snake_case` | `db_texts` |
| **Constante** | `UPPER_CASE` | `DEFAULT_DB_TEXTS` |
| **Função** | `snake_case` | `get_app_menu` |
| **Função Privada** ou **Local** | `_snake_case` | `_get_value` |


### Nota sobre a nomenclatura usada ###

Este guia segue as diretrizes da PEP 8 e da PEP 613 para Type Aliases padrão, adotando uma variação customizada (Snake_case) para os tipos definidos no aplicativo, visando evitar conflitos de nomenclatura.

### Dicas ###

  - **datetime** → the Python type from the datetime module (used in annotations)
  - **DateTime** → the SQLAlchemy column type (used in mapped_column)


#### _eof_