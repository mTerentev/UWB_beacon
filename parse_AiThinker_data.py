import numpy as np
import scipy as sp
import pandas as pd


def read_file_data(filename: str, min_num_of_measurements=10) -> pd.DataFrame:
    file = open(filename, mode='r', encoding='utf-8-sig')
    lines = file.readlines()
    file.close()
    # initialize a dictionary for all results to remember the tag and number of measurement
    dict_of_results = {}
    i = 0
    dict_blocks = {}

    for line in lines:
        # clear all garbage lines from the file
        if not line in ['\r\n', '\n', 'hello dwm1000!\n', 'init pass!\n', 'ERROR\n', 'AIT-BU01-DB V100 T2020-5-17\n',
                        'device:TAG ID:0\n']:
            # Use the "OK" line as splitter for data
            if 'OK' in line:
                # check did we collect any useful data before the "OK" line
                if dict_blocks:
                    name = list(dict_blocks.keys())[0]
                    # check is there a minimal number of measurements made before "OK" line
                    if len(dict_blocks[name]) >= min_num_of_measurements:
                        # copy all collected data into new item of the main dictionary
                        dict_of_results[i] = dict_blocks.copy()
                        # update number of collected measurements
                        i += 1
                    # clear the collecter to push data from new measurements
                    dict_blocks.clear()

            else:
                # split the name of tag and its results
                line = line.split(':')
                # delete m in all lines
                line = [i.strip().replace('m', '') for i in line]
                # check is the did we just clear collecter or there is something and check is the line in the right format
                if not line[0] in dict_blocks and len(line) > 1:
                    dict_blocks[line[0]] = [float(line[1])]
                else:
                    dict_blocks[line[0]].append(float(line[1]))

    # write all data into DataFrame
    df_or_results = pd.DataFrame.from_dict(dict_of_results, orient="index")
    return df_or_results


def get_array_from_df(dictionary, n_values_to_drop=5):
    np_array = dictionary.to_numpy()
    index = range(n_values_to_drop - 1)
    return [[np.delete(np.array(i), index), np.delete(np.array(j), index)] for i, j in np_array]




def calc_precision(x: np.array):
    return np.std(x)





def calc_dist_to_tags(dist: float, tr_angle: float, dist_btw_tags: float, in_degrees=True) -> list[float]:
    """
                ^
               /|\
      tr_side1/ | \tr_side2
             /  |d \
            /___|)__\
       l_tag  a ^    r_tag
                | mid_point_btw_tags
    :param dist: d
    :param tr_angle:
    :param dist_btw_tags:
    :param in_degrees: boolean, as default - True
    :return: tr_sides
    """

    if in_degrees:
        tr_angle = tr_angle * np.pi / 180
    # midpoint btw tags
    a = dist_btw_tags / 2

    # just a cosine law
    tr_side2 = np.sqrt(a ** 2 + dist ** 2 - 2 * a * dist * np.cos(tr_angle))
    tr_side1 = np.sqrt(a ** 2 + dist ** 2 - 2 * a * dist * np.cos(np.pi - tr_angle))

    return tr_side1, tr_side2


def calc_RMSE(x: np.ndarray, x_real: float) -> float:
    diff = x - x_real
    print(f"diff shspe: {diff.shape}")
    return np.sqrt(sum([diff[i] ** 2 for i in range(diff.shape[0])]) / diff.shape[0])


def calc_results(filename: str, array_of_results: np.ndarray, dictionary: dict = None, block_size: float = 0.6):
    # read data from the filename.
    filename = filename.split('/')[1]
    exp_info = filename.split("_")
    angl_is_positive = 1
    if "min" in exp_info[0]:
        print(exp_info[0])
        angl_is_positive = -1
        exp_info.pop(0)
    angle, angle_units, dist = [f"{i} " for i in exp_info[:3]]
    print(f"Exp info:\n\tAndle\tDistance btw tags (cm)\n\t{angle}{angle_units}\t{dist}")
    angle = np.pi / 2 - float(angle) * np.pi / 180 * angl_is_positive
    dist = float(dist) / 100

    return_dict = False
    if dictionary is not None:
        return_dict = True
        if not dist in dictionary:
            dictionary[dist] = {}

    for n_block in range(len(array_of_results)):
        real_dist_to_anchor = block_size * (n_block + 2) * np.sin(angle)
        truth_dist_to_tags = calc_dist_to_tags(dist=real_dist_to_anchor,
                                               tr_angle=angle, dist_btw_tags=dist, in_degrees=False)

        print(f"\tResults for {real_dist_to_anchor} m:")

        if return_dict:
            if not f'dist_to_anchor {real_dist_to_anchor}' in dictionary[dist]:
                dictionary[dist][f'dist_to_anchor {real_dist_to_anchor}'] = {}
            dictionary[dist][f'dist_to_anchor {real_dist_to_anchor}'][angle] = {}

        for n_tag in range(len(array_of_results[n_block])):
            rmse = calc_RMSE(array_of_results[n_block][n_tag], truth_dist_to_tags[n_tag])
            std = calc_precision(array_of_results[n_block][n_tag])

            estimated_val = np.mean(array_of_results[n_block][n_tag])

            print(f"\tTag {n_tag + 1}")
            print(f"\t\tTrue dist:\t\t\t{truth_dist_to_tags[n_tag]} m")
            print(f"\t\tEstimated dist:\t{estimated_val} m ")
            print(f"\t\tStandard deviation:\t{std * 100} cm")
            print(f"\t\tRMSE of measurement:\t{rmse} m")

            if return_dict:
                dictionary[dist][f'dist_to_anchor {real_dist_to_anchor}'][angle][f'tag {n_tag}'] = {"RMSE": rmse,
                                                                                                    "STD": std,
                                                                                                    "Estimated_val": estimated_val,
                                                                                                    "Truth_dist":
                                                                                                        truth_dist_to_tags[
                                                                                                            n_tag]}
    return dictionary