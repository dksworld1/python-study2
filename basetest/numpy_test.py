import numpy as np
import pandas as pd


def broadcast_test():
    # arr = np.random.randn(5, 3)
    arr = np.random.randn(3, 5)
    df = pd.DataFrame(arr)
    print(arr.shape[-1])
    print(arr)
    print(df.to_csv(index=False, header=False))

    # arr2 = np.random.randn(5,)
    arr2 = np.random.randn(5)
    print(arr2.shape)
    print(arr2)
    print(pd.DataFrame(arr2).to_csv(index=False, header=False))

    arr3 = np.random.randn(5, 1)
    print(arr3.shape)
    print(arr3)

    result = arr - arr2
    # result2 = arr2 * arr3
    print(result)


def arr2str_using_df_test():

    arr2 = np.random.randn(5)
    print('arr2.shape', arr2.shape, sep='\n', end='\n\n')
    print('arr2', arr2, sep='\n', end='\n\n')
    print('arr2 csv', pd.DataFrame(arr2).to_csv(index=False, header=False), sep='\n', end='\n\n')
    '''
    원하는 형태는 1,2,3,4,5 이나 1차원 ndarray는 df로 변환될때 컬럼하나로 들어가버림. 그래서 문자열로하면 1\n2\n.. 이렇게 됨.
    따라서 reshape 해주는게 필요함.
    '''
    if arr2.ndim == 1:
        arr3 = arr2.reshape(1, arr2.size)
    else:
        arr3 = arr2
    print('arr2 after reshape csv', pd.DataFrame(arr3).to_csv(index=False, header=False), sep='\n', end='\n\n')




if __name__ == '__main__':
    # broadcast_test()
    arr2str_using_df_test()
