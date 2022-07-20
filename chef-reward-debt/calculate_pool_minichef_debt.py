import argparse
import requests
import json
import pandas as pd
from web3 import Web3, HTTPProvider

GRAPH_ENDPOINTS = {
    'polygon': 'https://api.thegraph.com/subgraphs/name/sushiswap/matic-minichef',
    'xdai': 'https://api.thegraph.com/subgraphs/name/matthewlilley/xdai-minichef',
    'harmony': 'https://sushi.graph.t.hmny.io/subgraphs/name/sushiswap/harmony-minichef',
    'celo': 'https://api.thegraph.com/subgraphs/name/sushiswap/celo-minichef-v2',
    'moonriver': 'https://api.thegraph.com/subgraphs/name/sushiswap/moonriver-minichef',
    'arbitrum': 'https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-minichef',
    'fantom': 'https://api.thegraph.com/subgraphs/name/sushiswap/fantom-minichef',
    'fuse': 'https://api.thegraph.com/subgraphs/name/sushiswap/fuse-minichef',
}

RPC_ENDPOINTS = {
    'mainnet': 'https://mainnet.infura.io/v3/',
    'polygon': 'https://polygon-rpc.com/',
    'xdai': 'https://rpc.gnosischain.com',
    'harmony': 'https://api.harmony.one',
    'celo': 'https://forno.celo.org',
    'moonriver': 'https://rpc.moonriver.moonbeam.network',
    'arbitrum': 'https://arb1.arbitrum.io/rpc',
    'fantom': 'https://rpcapi.fantom.network',
    'fuse': 'https://rpc.fuse.io',
}


COMPLEX_REWADERS = {
    'polygon': '0xa3378ca78633b3b9b2255eaa26748770211163ae',
    'xdai': '0x3f505b5cff05d04f468db65e27e72ec45a12645f',
    'harmony': '0x25836011bbc0d5b6db96b20361a474cbc5245b45',
    'celo': '0xfa3de59edd2500ba725dad355b98e6a4346ada7d',
    'moonriver': '0x1334c8e873e1cae8467156e2a81d1c8b566b2da1',
    'fantom': '0xeaf76e3bd36680d98d254b378ed706cb0dfbfc1b',
    'fuse': '0xef502259dd5d497d082498912031e027c4515563',
}

def main(chain):

    graph_url = GRAPH_ENDPOINTS[chain]
    print(f'Pulling data from {chain} graph endpoint.')

    query = """query {
        pools (first: 100) {
            id
            pair
            users (first: 1000, where: {amount_gte: 0} orderBy: amount, orderDirection: desc) {
                address
            }
        }
        miniChefs(first: 1) {
            id
        }
    }
    """

    result = requests.post(graph_url, json={'query': query})
    data = json.loads(result.text)

    pool_data = data['data']['pools']
    minichef_address = data['data']['miniChefs'][0]['id']

    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[chain]))

    print(f'RPC is connected: {w3.isConnected}')
    print(f'Current block is: {w3.eth.blockNumber}')

    with open('../abis/MiniChef.json') as f:
        minichef_abi = json.load(f)

    with open('../abis/ComplexRewarder.json') as f:
        rewarder_abi = json.load(f)

    minichef_contract = w3.eth.contract(w3.toChecksumAddress(minichef_address), abi=minichef_abi)

    total_debt = 0

    for pool in pool_data:
        pid = int(pool['id'])
        pair_addy = pool['pair']
        user_data = pool['users']

        user_list = [
            entry['address']
            for entry in user_data
        ]

        #print(f'User List for pid: {int(pid)}\n')
        #print(user_list)

        pool_debt = 0
        print(f'Pulling pid: {int(pid)} pending Sushi.')
        for addy in user_list:
            try:
                pending = minichef_contract.functions.pendingSushi(pid, w3.toChecksumAddress(addy)).call()
            except:
                continue

            pool_debt += pending

        print(f'Pool {pid} Debt: {pool_debt / 1e18}')
        total_debt += (pool_debt / 1e18)

    print(f'Total Sushi Debt: {total_debt}')

    print(f'\nPulling rewarder native debt.')

    rewarder_contract = w3.eth.contract(w3.toChecksumAddress(COMPLEX_REWADERS[chain]), abi=rewarder_abi)

    total_rewarder_debt = 0

    for pool in pool_data:
        pid = int(pool['id'])
        pair_addy = pool['pair']
        user_data = pool['users']

        user_list = [
            entry['address']
            for entry in user_data
        ]

        pool_rewarder_debt = 0
        print(f'Pulling pid: {int(pid)} pending native tokens.')
        for addy in user_list:
            try:
                pending = rewarder_contract.functions.pendingToken(pid, w3.toChecksumAddress(addy)).call()
            except:
                continue

            pool_rewarder_debt += pending

        print(f'Pool {pid} Debt: {pool_rewarder_debt / 1e18}')
        total_rewarder_debt += (pool_rewarder_debt / 1e18)

    print(f'Total Native Debt: {total_rewarder_debt}')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process sushi debt for rewarders.")
    parser.add_argument('--chain', help="chain name")

    args = parser.parse_args()

    if args.chain == None : raise ValueError('Missing --chain in cmd arguments.')

    main(args.chain)
