# ZephyrusBot

The source code for a google cloud function (GCF) which checks the availability status of BestBuy products.

## Usage

```bash
git clone git@github.com:andrewrosss/zephyrus-bot.git
cd zephyrus-bot
```

To install the dependencies for this code into the active environment

```bash
poetry install
```

or if you don't have poetry

```bash
pip install -r requirements.txt
```

The code comes with a small CLI. To test that everything is working, first run:

```bash
python main.py --help
```

Then pass in a BestBuy product page

```bash
python main.py https://www.bestbuy.ca/en-ca/product/14335048
```
