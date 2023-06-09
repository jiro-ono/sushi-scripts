import argparse
import requests
import json
import pandas as pd
from web3 import Web3, HTTPProvider


GRAPH_ENDPOINTS = {
    'polygon': 'https://api.thegraph.com/subgraphs/name/sushiswap/matic-minichef',
    'gnosis': 'https://api.thegraph.com/subgraphs/name/sushiswap/minichef-gnosis',
    'harmony': 'https://sushi.graph.t.hmny.io/subgraphs/name/sushiswap/harmony-minichef',
    'celo': 'https://api.thegraph.com/subgraphs/name/sushiswap/celo-minichef-v2',
    'moonriver': 'https://api.thegraph.com/subgraphs/name/sushiswap/moonriver-minichef',
    'arbitrum': 'https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-minichef'
}

RPC_ENDPOINTS = {
    'mainnet': 'https://mainnet.infura.io/v3/',
    'polygon': 'https://polygon-rpc.com/',
    'gnosis': 'https://rpc.gnosischain.com',
    'harmony': 'https://api.harmony.one',
    'celo': 'https://forno.celo.org',
    'moonriver': 'https://rpc.moonriver.moonbeam.network',
    'arbitrum': 'https://arb1.arbitrum.io/rpc'
}


def main(chain):

    graph_url = GRAPH_ENDPOINTS[chain]
    print(f'Pulling data from {chain} graph endpoint.')

    query = """query {
        pools (first: 1000) {
            id
            pair
        }
        miniChefs(first: 1) {
            id
        }
    }
    """

    result = requests.post(graph_url, json={'query': query})
    data = json.loads(result.text)

    pools_data = data['data']['pools']
    minichef_address = data['data']['miniChefs'][0]['id']

    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINTS[chain]))

    print(f'RPC is connected: {w3.isConnected}')
    print(f'Current block is: {w3.eth.blockNumber}')

    with open('../abis/MiniChef.json') as f:
        minichef_abi = json.load(f)

    with open('../abis/Pair.json') as f:
        pair_abi = json.load(f)

    minichef_contract = w3.eth.contract(
        w3.toChecksumAddress(minichef_address), abi=minichef_abi)

    for pool in pools_data:
        pair_contract = w3.eth.contract(
            w3.toChecksumAddress(pool['pair']), abi=pair_abi)

        pool_info = minichef_contract.functions.poolInfo(
            int(pool['id'])).call()
        slp_balance = pair_contract.functions.balanceOf(
            w3.toChecksumAddress(minichef_address)).call()

        print(f"pid: {pool['id']}")
        print(f'Acc Sushi per Share: {pool_info[0] / 1e12}')
        print(f'Balance: {slp_balance / 1e18}')
        print(f"Debt: {(pool_info[0] / 1e12) * (slp_balance / 1e18)}")

    # for pool in pools_data:
    #    print(pool['id'])
    #    print(pool['pair'])

    '''
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
    '''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process sushi debt for rewarders.")
    parser.add_argument('--chain', help="chain name")

    args = parser.parse_args()

    if args.chain == None:
        raise ValueError('Missing --chain in cmd arguments.')

    main(args.chain)
