#AUTOGENERATED! DO NOT EDIT! File to edit: dev/09a_vision.data.ipynb (unless otherwise specified).

__all__ = ['ImageDataBunch', 'get_grid', 'clip_remove_empty', 'bb_pad', 'ImageBlock', 'MaskBlock', 'PointBlock',
           'BBoxBlock', 'BBoxBlock', 'BBoxLblBlock']

#Cell
from ..test import *
from ..torch_basics import *
from ..data.all import *

from .core import *

#Cell
class ImageDataBunch(DataBunch):

    @classmethod
    @delegates(DataBunch.from_dblock)
    def from_folder(cls, path, train='train', valid='valid', valid_pct=None, seed=None, vocab=None, **kwargs):
        "Create from imagenet style dataset in `path` with `train`,`valid`,`test` subfolders (or provide `valid_pct`)."
        splitter = GrandparentSplitter(train_name=train, valid_name=valid) if valid_pct is None else RandomSplitter(valid_pct, seed=seed)
        dblock = DataBlock(blocks=(ImageBlock, CategoryBlock(vocab=vocab)),
                           get_items=get_image_files,
                           splitter=splitter,
                           get_y=parent_label)
        return cls.from_dblock(dblock, path, path=path, **kwargs)

    @classmethod
    @delegates(DataBunch.from_dblock)
    def from_name_func(cls, path, fnames, label_func, valid_pct=0.2, seed=None, **kwargs):
        "Create from list of `fnames` in `path`s with `label_func`."
        dblock = DataBlock(blocks=(ImageBlock, CategoryBlock),
                           splitter=RandomSplitter(valid_pct, seed=seed),
                           get_y=label_func)
        return cls.from_dblock(dblock, fnames, path=path, **kwargs)

    @classmethod
    @delegates(DataBunch.from_dblock)
    def from_name_re(cls, path, fnames, pat, **kwargs):
        "Create from list of `fnames` in `path`s with re expression `pat`."
        return cls.from_name_func(path, fnames, RegexLabeller(pat), **kwargs)

    @classmethod
    @delegates(DataBunch.from_dblock)
    def from_df(cls, df, path='.', valid_pct=0.2, seed=None, fn_col=0, folder=None, suff='', label_col=1, label_delim=None, y_block=None, **kwargs):
        pref = f'{Path(path) if folder is None else Path(path)/folder}{os.path.sep}'
        if y_block is None: y_block = MultiCategoryBlock if is_listy(label_col) and len(label_col) > 1 else CategoryBlock
        dblock = DataBlock(blocks=(ImageBlock, y_block),
                           get_x=ColReader(fn_col, pref=pref, suff=suff),
                           get_y=ColReader(label_col, label_delim=label_delim),
                           splitter=RandomSplitter(valid_pct, seed=seed))
        return cls.from_dblock(dblock, df, path=path, **kwargs)

    @classmethod
    def from_csv(cls, path, csv_fname='labels.csv', header='infer', delimiter=None, **kwargs):
        df = pd.read_csv(Path(path)/csv_fname, header=header, delimiter=delimiter)
        return cls.from_df(df, path=path, **kwargs)

    @classmethod
    @delegates(DataBunch.from_dblock)
    def from_lists(cls, path, fnames, labels, valid_pct=0.2, seed:int=None, y_block=None, **kwargs):
        "Create from list of `fnames` in `path`."
        if y_block is None:
            y_block = MultiCategoryBlock if is_listy(labels[0]) and len(labels[0]) > 1 else (TransformBlock if isinstance(labels[0], float) else CategoryBlock)
        dblock = DataBlock(blocks=(ImageBlock, y_block),
                           splitter=RandomSplitter(valid_pct, seed=seed))
        return cls.from_dblock(dblock, (fnames, labels), path=path, **kwargs)

ImageDataBunch.from_csv = delegates(to=ImageDataBunch.from_df)(ImageDataBunch.from_csv)
ImageDataBunch.from_name_re = delegates(to=ImageDataBunch.from_name_func)(ImageDataBunch.from_name_re)

#Cell
def get_grid(n, rows=None, cols=None, add_vert=0, figsize=None, double=False, title=None, return_fig=False):
    rows = rows or int(np.ceil(math.sqrt(n)))
    cols = cols or int(np.ceil(n/rows))
    if double: cols*=2 ; n*=2
    figsize = (cols*3, rows*3+add_vert) if figsize is None else figsize
    fig,axs = subplots(rows, cols, figsize=figsize)
    axs = [ax if i<n else ax.set_axis_off() for i, ax in enumerate(axs.flatten())][:n]
    if title is not None: fig.suptitle(title, weight='bold', size=14)
    return (fig,axs) if return_fig else axs

#Cell
@typedispatch
def show_batch(x:TensorImage, y, samples, ctxs=None, max_n=10, rows=None, cols=None, figsize=None, **kwargs):
    if ctxs is None: ctxs = get_grid(min(len(samples), max_n), rows=rows, cols=cols, figsize=figsize)
    ctxs = show_batch[object](x, y, samples, ctxs=ctxs, max_n=max_n, **kwargs)
    return ctxs

#Cell
@typedispatch
def show_batch(x:TensorImage, y:TensorImage, samples, ctxs=None, max_n=10, rows=None, cols=None, figsize=None, **kwargs):
    if ctxs is None: ctxs = get_grid(min(len(samples), max_n), rows=rows, cols=cols, add_vert=1, figsize=figsize, double=True)
    for i in range(2):
        ctxs[i::2] = [b.show(ctx=c, **kwargs) for b,c,_ in zip(samples.itemgot(i),ctxs[i::2],range(max_n))]
    return ctxs

#Cell
def clip_remove_empty(bbox, label):
    "Clip bounding boxes with image border and label background the empty ones."
    bbox = torch.clamp(bbox, -1, 1)
    empty = ((bbox[...,2] - bbox[...,0])*(bbox[...,3] - bbox[...,1]) < 0.)
    return (bbox[~empty], label[~empty])

#Cell
def bb_pad(samples, pad_idx=0):
    "Function that collect `samples` of labelled bboxes and adds padding with `pad_idx`."
    samples = [(s[0], *clip_remove_empty(*s[1:])) for s in samples]
    max_len = max([len(s[2]) for s in samples])
    def _f(img,bbox,lbl):
        bbox = torch.cat([bbox,bbox.new_zeros(max_len-bbox.shape[0], 4)])
        lbl  = torch.cat([lbl, lbl .new_zeros(max_len-lbl .shape[0])+pad_idx])
        return img,bbox,lbl
    return [_f(*s) for s in samples]

#Cell
def ImageBlock(cls=PILImage): return TransformBlock(type_tfms=cls.create, batch_tfms=IntToFloatTensor)

#Cell
MaskBlock = TransformBlock(type_tfms=PILMask.create, batch_tfms=IntToFloatTensor)

#Cell
PointBlock = TransformBlock(type_tfms=TensorPoint.create, item_tfms=PointScaler)
BBoxBlock  = TransformBlock(type_tfms=TensorBBox.create,  item_tfms=PointScaler, dbunch_kwargs = {'before_batch': bb_pad})

#Cell
BBoxBlock = TransformBlock(type_tfms=TensorBBox.create, item_tfms=PointScaler, dbunch_kwargs = {'before_batch': bb_pad})

#Cell
def BBoxLblBlock(vocab=None, add_na=True):
    return TransformBlock(type_tfms=MultiCategorize(vocab=vocab, add_na=add_na), item_tfms=BBoxLabeler)