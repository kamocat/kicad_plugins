import pcbnew
import os
import wx

def get_sel():
    sel = pcbnew.GetCurrentSelection()
    for x in sel:
        print(x)
        if isinstance(x,pcbnew.FOOTPRINT):
            return x
        elif isinstance(x,pcbnew.PAD):
            return x.GetParent()
        else:
            print('not pad or footprint')

def get_lib(libname):
    lib = os.path.join(os.environ['KICAD7_FOOTPRINT_DIR']
                       ,libname+'.pretty')
    if os.path.isdir(lib):
        footprints = pcbnew.FootprintEnumerate(lib)
        return lib,footprints
    return None,None

def exchange_footprints(aExisting, aNew):
    aNew.SetParent(aExisting.GetParent())
    # FIXME: Place the footprint
    # pcbnew.PlaceFootprint(aNew, False) #But this function doesn't exist
    aNew.SetPosition(aExisting.GetPosition())
    if aNew.GetLayer() != aExisting.GetLayer():
        aNew.Flip(aNew.GetPosition(), True)
    if aNew.GetOrientation() != aExisting.GetOrientation():
        aNew.SetOrientation( aExisting.GetOrientation())
    aNew.SetLocked( aExisting.IsLocked())

    for pad in aNew.Pads():
        if pad.GetNumber() is None or not pad.IsOnCopperLayer():
            pad.SetNetCode(pcbnew.NETINFO_LIST.UNCONNECTED)
            continue
        last_pad = None
        while True:
            pad_model = aExisting.FindPadByNumber( pad.GetNumber(), last_pad )
            if pad_model is None:
                break
            if pad_model.IsOnCopperLayer():
                break
            last_pad = pad_model

        if pad_model is not None:
            pad.SetLocalRatsnestVisible( pad_model.GetLocalRatsnestVisible() )
            pad.SetPinFunction( pad_model.GetPinFunction())
            pad.SetPinType( pad_model.GetPinType())
            pad.SetNetCode( pad_model.GetNetCode() )
        else:
            pad.SetNetCode( pcbnew.NETINFO_LIST.UNCONNECTED )
    #TODO: Process text items
    #TODO: Copy fields
    #TODO: Copy UUID
    aNew.SetPath(aExisting.GetPath())
    #TODO: Remove aExisting from board commit
    #TODO: Add aNew to board commit
    aNew.ClearFlags()
    pcbnew.Refresh()


def next_fp(direction):
    # The entry function of the plugin that is executed on user action
    board = pcbnew.GetBoard()
    # TODO: Handle more than one item
    f = get_sel()
    if f is None:
        return
    fid = f.GetFPIDAsString()
    print(f'Selected {f.GetReference()} {fid}')
    libname,_,fpname = fid.partition(':')
    # Get the list of footprints from the library
    lib,footprints = get_lib(libname)
    i = footprints.index(fpname)
    i += direction
    if i < 0:
        i = 0
    elif i >= len(footprints):
        i = len(footprints)-1
    # Set the footprint to the next
    newfp = f'{libname}:{footprints[i]}'
    print(f'Changing to {newfp}')
    newfp = pcbnew.FootprintLoad(lib,footprints[i])
    exchange_footprints(f, newfp)
    print(f'Done')

def next_fp_callback(context):
    next_fp(1)

def prev_fp_callback(context):
    next_fp(-1)

def findPcbnewWindow():
    """Find the window for the PCBNEW application."""
    windows = wx.GetTopLevelWindows()
    pcbnew = [w for w in windows if "PCB Editor" in w.GetTitle()]
    if len(pcbnew) != 1:
        raise Exception("Cannot find pcbnew window from title matching!")
    return pcbnew[0]

class NextFp(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "next_footprint"
        self.category = "placement"
        self.description = "Cycles through footprints. Intended for changing resistor length while prototyping."
        self.show_toolbar_button = False # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'simple_plugin.png') # Optional, defaults to ""

    def Run(self):
        mainFrame = findPcbnewWindow()
        next_fp_button = wx.NewId()
        prev_fp_button = wx.NewId()
        test_button = wx.NewId()
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT,  ord('J'), next_fp_button )
                                         ,(wx.ACCEL_SHIFT,  ord('K'), prev_fp_button )
                                         ,(wx.ACCEL_SHIFT,  ord('M'), test_button)])
        mainFrame.Bind(wx.EVT_TOOL, next_fp_callback, id=next_fp_button)
        mainFrame.Bind(wx.EVT_TOOL, prev_fp_callback, id=prev_fp_button)
        mainFrame.Bind(wx.EVT_TOOL, get_sel, id=test_button)
        mainFrame.SetAcceleratorTable(accel_tbl)


NextFp().register() # Instantiate and register to Pcbnew
