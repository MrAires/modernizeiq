# Primary references

Checked 24 October 2026. These references support implementation choices and domain relevance; the package's feature/test claims come from its own code and executed verification.

- [Python 3.11 zipfile](https://docs.python.org/3.11/library/zipfile.html): archive reading APIs and resource considerations. ModernizeIQ uses bounded member reads and does not extract uploaded members.
- [Python 3.11 AST](https://docs.python.org/3.11/library/ast.html): syntax-tree parsing and traversal. ModernizeIQ uses parsing, not compilation/execution of target code.
- [Python 3.11 tomllib](https://docs.python.org/3.11/library/tomllib.html): standard-library TOML reading, available from Python 3.11.
- [Accenture application modernization](https://www.accenture.com/en/services/cloud/application-transformation/application-modernization): application assessment, architecture and roadmap context. Relevance does not imply hiring eligibility or a selection guarantee.
