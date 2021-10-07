from src.helpers import initializeParser
from src.optimizer import optimizeAllocations

if __name__ == '__main__':
    """
    main.py script to execute for command line interface. Runs the optimizeAllocations function
    """
    my_parser = initializeParser()
    args = my_parser.parse_args()

    optimizeAllocations(indexer_id=args.indexer_id, blacklist_parameter=args.blacklist,
                        parallel_allocations=args.parallel_allocations, max_percentage=args.max_percentage,
                        threshold=args.threshold, subgraph_list_parameter=args.subgraph_list,
                        threshold_interval=args.threshold_interval, reserve_stake=args.reserve_stake,
                        min_allocation=args.min_allocation, min_allocated_grt_subgraph=args.min_allocated_grt_subgraph,
                        min_signalled_grt_subgraph=args.min_signalled_grt_subgraph, app=args.app,
                        slack_alerting=args.slack_alerting, network=args.network, automation=args.automation, ignore_tx_costs=args.ignore_tx_costs)
