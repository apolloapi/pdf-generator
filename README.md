# pdf-generator

As a user I should be able to upload a data set, ask questions about my data and export my data into a pdf. The goal is to provide users the ability to generate transparency reports and chat with AI on my data to build the following, [transparency report example](https://transparency.fb.com/sr/india-monthly-report-jul31-2023/#:~:text=Between%201st%20and%2030th%20June,received%20under%20the%20following%20categories.&text=Of%20these%20incoming%20reports%2C%20we,their%20issues%20in%203%2C507%20cases)

### Setting up dev env
At this point you should've setup your virtual env

**Installation**

```
pip install -r requirements.txt
```

After installing system dependencies be sure to install pre-commit

```
pip install pre-commit

pre-commit install
```

**Contribution guidelines**

We use commit messages for automated generation of project changelog. For every pull request we request contributors to be compliant with the following commit message notation.

```
<type>: <summary>

<body>
```

Accepted <type> values:

- new = newly implemented user-facing features
- chg = changes in existing user-facing features
- fix = user-facing bugfixes
- oth = other changes which users should know about
- dev = any developer-facing changes, regardless of new/chg/fix status

Summary (The first line)
The first line should not be longer than 75 characters, the second line is always blank and other lines should be wrapped at 80 characters.
