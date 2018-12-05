import pandas as pd 
import time
import helper as hp 
from multiprocessing import Pool
from fetch import fetch

if __name__ == '__main__':
    
    region = 'pc-kakao'
    samples = hp.getRequest(region, 'samples', None, None)
    matches = samples['data']['relationships']['matches']['data']
    match_ids = [match['id'] for match in matches]

    print('DONE GETTING SAMPLE IDS, NOW STARTING TO PROCESS...')

    pool = Pool(3)
    batches = [match_ids[1000*i:1000*i+1000] for i in range(0, 10)]

    for i, batch in enumerate(batches):
        start_time = time.time()

        pooled = pool.map(fetch, batch)
        gap = """

        ---------------------------------------------------------------

        """
        print(gap, 'LEGTH: ', len(pooled), gap)
        for df in pooled:
            if not df.empty:
                with open('solo_san.csv', 'a') as f:
                    df.to_csv(f, index=False, header=False)

        took = time.time() - start_time
        print('PROCESS #%i DONE. TOOK %f SECONDS' % (i, took))
