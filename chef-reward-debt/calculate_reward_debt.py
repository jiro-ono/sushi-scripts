import argparse
import requests
import json
import pandas as pd
from web3 import Web3, HTTPProvider

GRAPH_ENDPOINTS = {
    'mainnet': 'https://api.thegraph.com/subgraphs/name/sushiswap/master-chefv2',
    'polygon': 'https://api.thegraph.com/subgraphs/name/sushiswap/matic-minichef',
    'xdai': 'https://api.thegraph.com/subgraphs/name/matthewlilley/xdai-minichef',
    'harmony': 'https://sushi.graph.t.hmny.io/subgraphs/name/sushiswap/harmony-minichef',
    'celo': 'https://api.thegraph.com/subgraphs/name/sushiswap/celo-minichef',
    'moonriver': 'https://api.thegraph.com/subgraphs/name/sushiswap/moonriver-minichef',
    'arbitrum': 'https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-minichef'
}

RPC_ENDPOINTS = {
    'mainnet': 'https://mainnet.infura.io/v3/',
    'polygon': 'https://polygon-rpc.com/',
    'xdai': 'https://rpc.xdaichain.com',
    'harmony': 'https://api.harmony.one',
    'celo': 'https://forno.celo.org',
    'moonriver': 'https://rpc.moonriver.moonbeam.network',
    'arbitrum': 'https://arb1.arbitrum.io/rpc'
}

def main(chain, pid, decimals):

    graph_url = GRAPH_ENDPOINTS[chain]
    print(f'Pulling data from {chain} graph endpoint.')


    query = """query chefQuery($pid: String!) {
        pool(id: $pid) {
            id
            users (first: 1000) {
                address
            }
            rewarder {
                id
            }
        }
    }
    """
    variables = {'pid': str(pid)}

    result = requests.post(graph_url, json={'query': query, 'variables': variables})
    data = json.loads(result.text)

    df_data = data['data']['pool']['users']

    user_list = [
        entry['address']
        for entry in data['data']['pool']['users']
    ]

    rewarder_addy = data['data']['pool']['rewarder']['id']
    print(f'Rewarder address: {rewarder_addy}')

    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[chain]))

    print(f'RPC is connected: {w3.isConnected}')
    print(f'Current block is: {w3.eth.blockNumber}')

    with open('../abis/Rewarder.json') as f:
        rewarder_abi = json.load(f)


    rewarder_contract = w3.eth.contract(w3.toChecksumAddress(rewarder_addy), abi=rewarder_abi)

    total_debt = 0
    debt_dict = {}

    for addy in user_list:
        pending = rewarder_contract.functions.pendingToken(pid, w3.toChecksumAddress(addy)).call()
        total_debt += pending

        debt_dict[addy] = (pending / 10**decimals)

    print('\nUser List:\n')
    print(user_list)
    print('\nUser Amounts:\n')
    print(json.dumps(debt_dict, indent=1))
    print(f'\nTotal Debt: {total_debt / 10**decimals}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process sushi debt for rewarders.")
    parser.add_argument('--chain', help="chain name")
    parser.add_argument('--pid', help="pool id", type=int)
    parser.add_argument('--decimals', help="reward token decimals", type=int)

    args = parser.parse_args()

    if args.chain == None : args.chain = 'mainnet'
    if args.decimals == None : args.decimals = 18
    if args.pid == None : raise ValueError('Missing --pid in cmd arguments.')

    main(args.chain, args.pid, args.decimals)
