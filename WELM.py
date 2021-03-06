"""
WELM as given in:
A Robust Indoor Positioning System Based on the
Procrustes Analysis and Weighted Extreme Learning Machine
Paper Authors By: Han Zou, Baoqi Huang, Xiaoxuan Lu, Hao Jiang, Lihua Xie
"""
import numpy as np


class ActFunc:
    # triangular activation function
    tribas = (lambda x: np.clip(1.0 - np.fabs(x), 0.0, 1.0))

    # inverse triangular activation function
    inv_tribas = (lambda x: np.clip(np.fabs(x), 0.0, 1.0))

    # sigmoid activation function
    sigmoid = (lambda x: 1.0 / (1.0 + np.exp(-x)))

    # hard limit activation function
    hardlim = (lambda x: (x > 0) * 1.0)

    softlim = (lambda x: np.clip(x, 0.0, 1.0))

    # sine function
    sin = np.sin

    # sine function
    tanh = np.tanh


class WelmRegressor:
    """
    class for WELM Regressor.
    """

    def __init__(self, train_mat, output_mat, activation_function,
                 num_hidden_neuron, hyper_param_c, weight_mat=None):

        self.train_mat = np.matrix(train_mat)
        self.t_mat = np.matrix(output_mat)

        assert self.train_mat.shape[0] is output_mat.shape[0], \
            "input and output should have same number of rows"

        # number of training data is rows of input matrix
        # M
        self.num_train_data = self.train_mat.shape[0]

        # number of input neuron is number of columns in input matrix
        self.num_input_neurons = self.train_mat.shape[1]

        # if weight matrix is not given then generate it
        # use constants Weights as diag(1)
        # W
        if weight_mat is None:
            self.w_mat = np.identity(self.num_train_data)
        else:
            self.w_mat = weight_mat

        # get the number of hidden neurons
        # L
        self.num_hidden_neuron = num_hidden_neuron

        # get the activation function
        # G
        self.activation_function = activation_function

        # set hyper parameter
        # C
        self.hyper_param_c = hyper_param_c

        # set input weigth and bias
        self.input_weight, self.bias_of_hidden_neurons = self.__get_input_weight_and_bias__()
        # print("Input Weight Shape: ", self.input_weight.shape)

        # build H matrix
        self.h_mat = self.__build_hidden_layer_output_matrix__(self.train_mat)
        # print("H shape:", self.h_mat.shape)

        # build \beta matrix
        self.beta_mat = self.__build_output_weight_matrix__()
        # print("beta shape:", self.beta_mat.shape)

        # trained output
        # this matrix should be choose to training data
        self.trained_output_mat = self.h_mat * self.beta_mat
        # print("T shape: ", self.trained_output_mat.shape)

    def get_projected(self, test_mat):
        """
        get projected output from NN
        """
        # # the shape of test_mat should match shape of train_mat
        # columns sholuld be same
        assert self.train_mat.shape[1] == test_mat.shape[1], "train-test column mismatch"

        h_mat_test = self.__build_hidden_layer_output_matrix__(test_mat)
        output_mat = h_mat_test * self.beta_mat

        return output_mat

    def get_trained_accuracy(self):
        """
        get the RMSE value of the trained model
        """
        return WelmRegressor.rmse(self.trained_output_mat, self.t_mat)

    def get_trained_average_distance(self):
        """
        get the average euclidean distance between model created and training data
        """
        return WelmRegressor.aed(self.trained_output_mat, self.t_mat)

    @staticmethod
    def aed(predictions, targets, dimensions=2, conversion_factor=1):
        """
        get the average euclidean distance between prediction and target
        """
        predictions = np.array(predictions).reshape(-1, dimensions)
        targets = np.array(targets).reshape(-1, dimensions)

        # print(predictions, targets)

        return np.sqrt(np.sum(np.square(predictions - targets), axis=1)).mean() / conversion_factor

    @staticmethod
    def eds(predictions, targets, dimensions=2, conversion_factor=1):
        """
        get the euclidean distances between prediction and target
        """
        predictions = np.array(predictions).reshape(-1, dimensions)
        targets = np.array(targets).reshape(-1, dimensions)

        # print(predictions, targets)

        return np.sqrt(np.sum(np.square(predictions - targets), axis=1)) / conversion_factor

    @staticmethod
    def rmse(predictions, targets):
        """
        get the RMSE between prediction and target
        based on sklearn.metrics.mean_squared_error
        """
        out_errors = np.average(np.square((predictions - targets)), axis=0)
        return np.average(out_errors)

    def __get_input_weight_and_bias__(self):
        input_weight = np.random.rand(
            self.num_hidden_neuron, self.num_input_neurons) * 2 - 1

        bias_of_hidden_neurons = np.random.rand(self.num_hidden_neuron, 1)

        return input_weight, bias_of_hidden_neurons

    def __build_hidden_layer_output_matrix__(self, data_mat):

        # between -1 to 1
        temp_h = np.dot(self.input_weight, data_mat.transpose())

        # shape of H matrix and bias matrix should match
        # create two more columns fo ones
        ones = np.ones(
            [
                self.bias_of_hidden_neurons.shape[0],
                data_mat.shape[0] - self.bias_of_hidden_neurons.shape[1]
            ], )
        bias_matrix = np.append(self.bias_of_hidden_neurons, ones, axis=1)

        temp_h = temp_h + bias_matrix

        # the matrix in paper is actually
        # the transpose of the matrix created
        temp_h = np.transpose(temp_h)

        return self.activation_function(temp_h)

    def __build_output_weight_matrix__(self):
        if self.num_train_data < self.num_hidden_neuron:
            return self.__beta_l_is_greater_than_m__()
        else:
            return self.__beta_m_is_greater_than_l__()

    def __beta_m_is_greater_than_l__(self):
        inner_mat = self.h_mat.transpose() * self.w_mat * self.h_mat

        i_by_c = np.identity(inner_mat.shape[0]) / self.hyper_param_c

        sum_inner_c_mat = inner_mat + i_by_c

        outer_mat = self.h_mat.transpose() * self.w_mat * self.t_mat

        return np.linalg.lstsq(sum_inner_c_mat, outer_mat)[0]

    def __beta_l_is_greater_than_m__(self):
        # print("L > M or M < L")

        # print("inner - W", self.w_mat.shape, "H", self.h_mat.shape)
        inner_mat = self.w_mat * self.h_mat * self.h_mat.transpose()
        # print("inner shape:", inner_mat.shape)

        i_by_c = np.identity(self.t_mat.shape[0]) / self.hyper_param_c
        # print("I/C shape:", i_by_c.shape)

        sum_inner_c_mat = inner_mat + i_by_c
        # print("sum inner mat shape:", sum_inner_c_mat.shape)
        # print("T shape:", self.t_mat.shape)

        w_mat_dot_t_mat = self.w_mat * self.t_mat

        return self.h_mat.transpose() * np.linalg.lstsq(sum_inner_c_mat, w_mat_dot_t_mat)[0]
