# Page snapshot

```yaml
- generic [ref=e1]:
  - main [ref=e4]:
    - img "Dashboard illustration" [ref=e6]
    - generic [ref=e10]:
      - generic [ref=e11]:
        - heading "Welcome" [level=4] [ref=e12]
        - paragraph [ref=e13]: Sign in to continue to your account
      - generic [ref=e14]:
        - generic [ref=e15]:
          - generic [ref=e16]: Email address
          - generic [ref=e17]:
            - img [ref=e19]
            - textbox "Email address" [active] [ref=e21]
            - group:
              - generic: Email address
        - button "Continue" [ref=e22] [cursor=pointer]: Continue
  - region "Notifications alt+T":
    - list:
      - status [ref=e23]:
        - button "Close toast" [ref=e24] [cursor=pointer]:
          - img [ref=e25]
        - img [ref=e29]
        - generic [ref=e32]: Services are healthy
```