"""Unit tests for the rectorch.models.nn module
"""
import os
import sys
import tempfile
import pytest
import torch
import numpy as np
from scipy.sparse import csr_matrix
sys.path.insert(0, os.path.abspath('..'))

from rectorch.models import RecSysModel
from rectorch.models.nn import TorchNNTrainer, AETrainer, VAE, MultiDAE, MultiVAE,\
    CMultiVAE, EASE, CFGAN, ADMM_Slim, SVAE
from rectorch.nets import MultiDAE_net, VAE_net, MultiVAE_net, CMultiVAE_net, CFGAN_D_net,\
    CFGAN_G_net, SVAE_net
from rectorch.samplers import DataSampler, ConditionedDataSampler, CFGAN_TrainingSampler,\
    SVAE_Sampler

def test_RecSysModel():
    """Test the RecSysModel class
    """
    model = RecSysModel()

    with pytest.raises(NotImplementedError):
        model.train(None)
    with pytest.raises(NotImplementedError):
        model.predict(None)
    with pytest.raises(NotImplementedError):
        model.save_model(None)
    with pytest.raises(NotImplementedError):
        model.load_model(None)

def test_TorchNNTrainer():
    """Test the TorchNNTrainer class
    """
    net = MultiDAE_net([1, 2], [2, 1], .1)
    model = TorchNNTrainer(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam),\
        "optimizer should be of type torch.optim.Adam"
    assert str(model) == repr(model)

    x = torch.FloatTensor([[1, 1], [2, 2]])
    with pytest.raises(NotImplementedError):
        model.loss_function(None, None)
        model.train(None, None)
        model.train_epoch(0, None)
        model.train_batch(0, None, None)
        model.predict(x)


def test_AETrainer():
    """Test the AETrainer class
    """
    net = MultiDAE_net([1, 2], [2, 1], .1)
    model = AETrainer(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    gt = torch.FloatTensor([[1, 1], [2, 1]])
    pred = torch.FloatTensor([[1, 1], [1, 1]])
    assert model.loss_function(pred, gt) == torch.FloatTensor([.25]), "the loss should be .25"

    values = np.array([1., 1., 1.])
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 1])
    train = csr_matrix((values, (rows, cols)))
    sampler = DataSampler(train, batch_size=1, shuffle=False)

    x = torch.FloatTensor([[1, 1], [2, 2]])
    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=20, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = MultiDAE_net([1, 2], [2, 1], .1)
    model2 = AETrainer(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"

    sampler = DataSampler(train, train, batch_size=1, shuffle=False)

def test_VAE():
    """Test the VAE class
    """
    net = VAE_net([1, 2], [2, 1])
    model = VAE(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    gt = torch.FloatTensor([[1, 1], [2, 1]])
    pred = torch.FloatTensor([[1, 1], [1, 1]])
    torch.manual_seed(12345)
    mu, logvar = model.network.encode(gt)
    pred = torch.sigmoid(pred)
    assert model.loss_function(pred, gt, mu, logvar) != torch.FloatTensor([.0]),\
        "the loss should not be 0"

    values = np.array([1., 1., 1.])
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 1])
    train = csr_matrix((values, (rows, cols)))
    sampler = DataSampler(train, batch_size=1, shuffle=False)

    x = torch.FloatTensor([[1, 1], [2, 2]])
    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=10, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = VAE_net([1, 2], [2, 1])
    model2 = VAE(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"

def test_MultiDAE():
    """Test the MultiDAE class
    """
    net = MultiDAE_net([1, 2], [2, 1], dropout=.1)
    model = MultiDAE(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert hasattr(model, "lam"), "model should have the attribute lam"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert model.lam == .2, "lambda should be .2"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    gt = torch.FloatTensor([[1, 1], [2, 1]])
    pred = torch.FloatTensor([[1, 1], [1, 1]])
    torch.manual_seed(12345)
    assert model.loss_function(pred, gt) != torch.FloatTensor([.0]),\
        "the loss should not be 0"

    values = np.array([1., 1., 1.])
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 1])
    train = csr_matrix((values, (rows, cols)))
    sampler = DataSampler(train, batch_size=1, shuffle=False)

    x = torch.FloatTensor([[1, 1], [2, 2]])
    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=10, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = MultiDAE_net([1, 2], [2, 1], dropout=.1)
    model2 = MultiDAE(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"


def test_MultiVAE():
    """Test the MultiVAE class
    """
    net = MultiVAE_net([1, 2], [2, 1], .1)
    model = MultiVAE(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    gt = torch.FloatTensor([[1, 1], [2, 1]])
    pred = torch.FloatTensor([[1, 1], [1, 1]])
    torch.manual_seed(12345)
    mu, logvar = model.network.encode(gt)
    pred = torch.sigmoid(pred)
    assert model.loss_function(pred, gt, mu, logvar) != torch.FloatTensor([.0]),\
        "the loss should not be 0"

    values = np.array([1., 1., 1.])
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 1])
    train = csr_matrix((values, (rows, cols)))
    sampler = DataSampler(train, batch_size=1, shuffle=False)

    x = torch.FloatTensor([[1, 1], [2, 2]])
    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=10, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = MultiVAE_net([1, 2], [2, 1], .1)
    model2 = MultiVAE(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"

    sampler = DataSampler(train, train, batch_size=1, shuffle=False)

    tmp2 = tempfile.NamedTemporaryFile()
    net = MultiVAE_net([1, 2], [2, 1], .1)
    model = MultiVAE(net, 1., 5)
    model.train(sampler,
                valid_data=sampler,
                valid_metric="ndcg@1",
                num_epochs=10,
                best_path=tmp2.name)

    net2 = MultiVAE_net([1, 2], [2, 1], .1)
    model2 = MultiVAE(net2, 1., 5)
    assert model2.gradient_updates == 0,\
        "after initialization there should not be any gradient updates"
    model2.load_model(tmp2.name)
    assert model2.gradient_updates > 0,\
        "the loaded model should have been saved after some gradient updates"


def test_CMultiVAE():
    """Test the CMultiVAE class
    """
    values = np.array([1., 1., 1., 1.])
    rows = np.array([0, 0, 1, 1])
    cols = np.array([0, 1, 1, 2])
    train = csr_matrix((values, (rows, cols)))

    iid2cids = {0:[1], 1:[0, 1], 2:[0]}
    sampler = ConditionedDataSampler(iid2cids, 2, train, batch_size=2, shuffle=False)

    net = CMultiVAE_net(2, [1, 3], dropout=.1)
    model = CMultiVAE(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    x = torch.FloatTensor([[1, 1, 0, 1, 0], [1, 0, 0, 0, 1]])
    gt = torch.FloatTensor([[1, 1, 1], [2, 1, 1]])
    pred = torch.FloatTensor([[1, 1, 1], [1, 1, 1]])
    torch.manual_seed(12345)
    mu, logvar = model.network.encode(x)
    pred = torch.sigmoid(pred)
    assert model.loss_function(pred, gt, mu, logvar) != torch.FloatTensor([.0]),\
        "the loss should not be 0"

    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=10, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = CMultiVAE_net(2, [1, 3], dropout=.1)
    model2 = CMultiVAE(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"

    tmp2 = tempfile.NamedTemporaryFile()
    net = CMultiVAE_net(2, [1, 3], [3, 1], .1)
    model = CMultiVAE(net, 1., 5)
    model.train(sampler,
                valid_data=sampler,
                valid_metric="ndcg@1",
                num_epochs=10,
                best_path=tmp2.name)

    net2 = CMultiVAE_net(2, [1, 3], [3, 1], .1)
    model2 = CMultiVAE(net2, 1., 5)
    assert model2.gradient_updates == 0,\
        "after initialization there should not be any gradient updates"
    model2.load_model(tmp2.name)
    assert model2.gradient_updates > 0,\
        "the loaded model should have been saved after some gradient updates"


def test_EASE():
    """Test the EASE class
    """
    ease = EASE(200.)
    assert hasattr(ease, "lam"), "ease should have the attribute lam"
    assert hasattr(ease, "model"), "ease should have the attribute model"
    assert ease.lam == 200, "lambda should be 200"
    assert ease.model is None, "before the training the inner model should be None"
    assert repr(ease) == str(ease)

    X = csr_matrix(np.random.randint(2, size=(10, 5)), dtype="float64")
    ease.train(X)
    assert isinstance(ease.model, np.ndarray), "after training the model should be a numpy matrix"
    pr = ease.predict([2, 4, 5], X[[2, 4, 5]])[0]
    assert pr.shape == (3, 5), "the shape of the prediction whould be 3 x 5"
    tmp = tempfile.NamedTemporaryFile()
    ease.save_model(tmp.name)
    ease2 = EASE(200.)
    ease2.load_model(tmp.name + ".npy")
    assert np.all(ease2.model == ease.model), "the two model should be the same"
    os.remove(tmp.name + ".npy")
    assert repr(ease) == str(ease)

def test_CFGAN():
    """Test of the CFGAN class
    """
    n_items = 3
    gen = CFGAN_G_net([n_items, 5, n_items])
    disc = CFGAN_D_net([n_items*2, 5, 1])
    cfgan = CFGAN(gen, disc, alpha=.03, s_pm=.5, s_zr=.7)

    assert hasattr(cfgan, "generator")
    assert hasattr(cfgan, "discriminator")
    assert hasattr(cfgan, "s_pm")
    assert hasattr(cfgan, "s_zr")
    assert hasattr(cfgan, "loss")
    assert hasattr(cfgan, "alpha")
    assert hasattr(cfgan, "n_items")
    assert hasattr(cfgan, "opt_g")
    assert hasattr(cfgan, "opt_d")
    assert cfgan.generator == gen
    assert cfgan.discriminator == disc
    assert cfgan.s_pm == .5
    assert cfgan.s_zr == .7
    assert cfgan.alpha == .03
    assert cfgan.n_items == 3
    assert isinstance(cfgan.loss, torch.nn.BCELoss)
    assert isinstance(cfgan.regularization_loss, torch.nn.MSELoss)
    assert isinstance(cfgan.opt_d, torch.optim.Adam)
    assert isinstance(cfgan.opt_g, torch.optim.Adam)

    values = np.array([1., 1., 1., 1.])
    rows = np.array([0, 0, 1, 1])
    cols = np.array([0, 1, 1, 2])
    train = csr_matrix((values, (rows, cols)))
    sampler = CFGAN_TrainingSampler(train, 1)

    values = np.array([1.])
    rows = np.array([0])
    cols = np.array([0])
    val_tr = csr_matrix((values, (rows, cols)), shape=(1, 3))

    cols = np.array([1])
    val_te = csr_matrix((values, (rows, cols)), shape=(1, 3))

    vsampler = DataSampler(val_tr, val_te, batch_size=1, shuffle=False)
    cfgan.train(sampler, vsampler, "ndcg@1", num_epochs=10, g_steps=1, d_steps=1, verbose=4)
    pred = cfgan.predict(torch.FloatTensor([[0, 1, 1], [1, 1, 0]]))[0]
    assert pred.shape == (2, 3)

    tmp = tempfile.NamedTemporaryFile()
    cfgan.save_model(tmp.name, 10)

    gen2 = CFGAN_G_net([n_items, 5, n_items])
    disc2 = CFGAN_D_net([n_items*2, 5, 1])
    cfgan2 = CFGAN(gen2, disc2, alpha=.03, s_pm=.5, s_zr=.7)
    chkpt = cfgan2.load_model(tmp.name)
    assert chkpt["epoch"] == 10
    assert cfgan2.generator != gen
    assert cfgan2.discriminator != disc
    assert str(cfgan) == repr(cfgan)

def test_ADMM_Slim():
    """Test the ADMM_Slim class
    """
    slim = ADMM_Slim(lambda1=5.,
                     lambda2=1e3,
                     rho=1e5,
                     nn_constr=True,
                     l1_penalty=True,
                     item_bias=False)
    assert hasattr(slim, "lambda1"), "admm_slim should have the attribute lambda1"
    assert hasattr(slim, "lambda2"), "admm_slim should have the attribute lambda2"
    assert hasattr(slim, "rho"), "admm_slim should have the attribute rho"
    assert hasattr(slim, "l1_penalty"), "admm_slim should have the attribute l1_penalty"
    assert hasattr(slim, "nn_constr"), "admm_slim should have the attribute nn_constr"
    assert hasattr(slim, "item_bias"), "admm_slim should have the attribute item_bias"
    assert hasattr(slim, "model"), "sladmm_slimim should have the attribute model"
    assert slim.lambda1 == 5, "lambda1 should be 5"
    assert slim.lambda2 == 1e3, "lambda2 should be 1000"
    assert slim.rho == 1e5, "rho should be 10000"
    assert slim.nn_constr, "nn_constr should be True"
    assert slim.l1_penalty, "l1_penalty should be True"
    assert not slim.item_bias, "item_bias should be False"
    assert slim.model is None, "before the training the inner model should be None"
    assert repr(slim) == str(slim)

    X = csr_matrix(np.random.randint(2, size=(10, 5)), dtype="float64")
    slim.train(X)
    assert isinstance(slim.model, np.ndarray), "after training the model should be a numpy matrix"
    pr = slim.predict([2, 4, 5], X[[2, 4, 5]])[0]
    assert pr.shape == (3, 5), "the shape of the prediction whould be 3 x 5"
    tmp = tempfile.NamedTemporaryFile()
    slim.save_model(tmp.name)
    slim2 = ADMM_Slim()
    slim2.load_model(tmp.name + ".npy")
    assert np.all(slim2.model == slim.model), "the two model should be the same"
    os.remove(tmp.name + ".npy")
    assert repr(slim) == str(slim)

    slim2 = ADMM_Slim(nn_constr=False, l1_penalty=True, item_bias=False)
    slim2.train(X)
    slim2 = ADMM_Slim(nn_constr=True, l1_penalty=False, item_bias=False)
    slim2.train(X)
    slim2 = ADMM_Slim(nn_constr=False, l1_penalty=False, item_bias=False)
    slim2.train(X)
    slim2 = ADMM_Slim(nn_constr=False, l1_penalty=False, item_bias=True)
    slim2.train(X)


def test_SVAE():
    """Test the SVAE class
    """
    total_items = 7
    net = SVAE_net(n_items=total_items,
                   embed_size=2,
                   rnn_size=2,
                   dec_dims=[2, total_items],
                   enc_dims=[2, 2])
    model = SVAE(net)

    assert hasattr(model, "network"), "model should have the attribute newtork"
    assert hasattr(model, "device"), "model should have the attribute device"
    assert hasattr(model, "optimizer"), "model should have the attribute optimizer"
    assert model.network == net, "the network should be the same as the parameter"
    assert model.device == torch.device("cpu"), "the device should be cpu"
    assert isinstance(model.optimizer, torch.optim.Adam), "optimizer should be of Adam type"
    assert str(model) == repr(model), "repr and str should have the same effect"

    tr = {0:[0, 1, 2, 3, 4, 5, 6], 1:[6, 5, 4, 3, 2, 1, 0], 2:[2, 1, 6, 0, 3]}
    sampler = SVAE_Sampler(num_items=total_items,
                           dict_data_tr=tr,
                           dict_data_te=None,
                           pred_type="next",
                           k=2,
                           shuffle=False,
                           is_training=True)

    x = torch.LongTensor([[1, 2, 5]])
    model.predict(x, True)
    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    model.train(sampler, num_epochs=10, verbose=4)
    torch.manual_seed(12345)
    out_2 = model.predict(x, False)[0]

    assert not torch.all(out_1.eq(out_2)), "the outputs should be different"

    tmp = tempfile.NamedTemporaryFile()
    model.save_model(tmp.name, 1)

    net = SVAE_net(n_items=total_items,
                   embed_size=2,
                   rnn_size=2,
                   dec_dims=[2, total_items],
                   enc_dims=[2, 2])
    model2 = SVAE(net)
    model2.load_model(tmp.name)

    torch.manual_seed(12345)
    out_1 = model.predict(x, False)[0]
    torch.manual_seed(12345)
    out_2 = model2.predict(x, False)[0]
    assert torch.all(out_1.eq(out_2)), "the outputs should be the same"
