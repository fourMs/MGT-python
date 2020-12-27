import musicalgestures
from musicalgestures._utils import MgFigure, MgImage


class MgList():
    """
    Class for handling lists of MgImage, MgFigure and MgList objects in the Musical Gestures Toolbox.

    Attributes
    ----------
    - *objectlist : objects and/or list(s) of objects

        MgObjects and/or MgImages to include in the list.
    """

    def __init__(self, *objectlist):
        """
        Initializes the MgList object.

        Args:
            *objectlist (MgImage, MgFigure or MgList): All the objects to include in the MgList.
        """

        def crawler(l):
            """
            Helper function to flatten all arguments into a single list.

            Args:
                l (list): The list (or list of lists) of objects.

            Returns:
                list: The flattened list.
            """
            _tmp = []
            for elem in l:
                if type(elem) == list:
                    _tmp += crawler(elem)
                else:
                    _tmp.append(elem)
            return _tmp

        self.objectlist = crawler(objectlist)

    from musicalgestures._show import mg_show
    from musicalgestures._utils import MgFigure, MgImage

    def show(self, filename=None, key=None, mode='windowed', window_width=640, window_height=480, window_title=None):
        """
        Iterates all objects in the MgList and calls `mg_show()` on them.
        """
        for obj in self.objectlist:
            if type(obj) != MgFigure:
                obj.show(filename=filename, key=key, mode=mode, window_width=window_width,
                         window_height=window_height, window_title=window_title)
            else:
                obj.show()

    def __len__(self):
        """
        Implements `len()`.

        Returns:
            int: The length of the MgList.
        """
        return len(self.objectlist)

    def __getitem__(self, key):
        """
        Implements getting elements given an index from the MgList.

        Args:
            key (int): The index of the element to retrieve.

        Returns:
            MgImage, MgFigure, or MgList: The element at `key`.
        """
        return self.objectlist[key]

    def __setitem__(self, key, value):
        """
        Implements setting elements given an index from the MgList.

        Args:
            key (int): The index of the element to change.
            value (MgImage, MgFigure, or MgList): The element to place at `key`.
        """
        self.objectlist[key] = value

    def __delitem__(self, key):
        """
        Implements deleting elements given an index from the MgList.

        Args:
            key (int): The index of the element to delete.
        """
        del self.objectlist[key]

    def __iter__(self):
        """
        Implements `iter()`.

        Returns:
            iterator: The iterator of `self.objectlist`.
        """
        return iter(self.objectlist)

    def __iadd__(self, other):
        """
        Implements `+=`.

        Args:
            other (MgImage, MgFigure, or MgList): The object(s) to add to the MgList.

        Returns:
            MgList: The incremented MgList.
        """
        if type(other) == MgList:
            self.objectlist += other.objectlist
        elif type(other) == list:
            for ind, elem in enumerate(other):
                if type(elem) in [MgList, MgImage, MgFigure]:
                    self.objectlist.append(elem)
                else:
                    print(
                        f'Incompatible object type {type(elem)} at index {ind}, ignoring it.')
        elif type(other) in [MgList, MgImage, MgFigure]:
            self.objectlist.append(other)
        else:
            print(f'Incompatible object type {type(other)}, ignoring it.')
        return MgList(self.objectlist)

    def __add__(self, other):
        """
        Implements `+`.

        Args:
            other (MgImage, MgFigure, or MgList): The object(s) to add to the MgList.

        Returns:
            MgList: The incremented MgList.
        """
        if type(other) == MgList:
            return MgList(self.objectlist + other.objectlist)
        elif type(other) == list:
            _tmp_list = []
            _tmp_list += self.objectlist
            for ind, elem in enumerate(other):
                if type(elem) in [MgList, MgImage, MgFigure]:
                    _tmp_list += elem
                else:
                    print(
                        f'Incompatible object type {type(elem)} at index {ind}, ignoring it.')
            return MgList(_tmp_list)
        elif type(other) in [MgList, MgImage, MgFigure]:
            return MgList(self.objectlist + other)
        else:
            print(f'Incompatible object type {type(other)}, ignoring it.')
            return MgList(self.objectlist)

    def __repr__(self):
        return f"MgList('{self.objectlist}')"

    def as_figure(self, dpi=300, autoshow=True, title=None, export_png=True):
        """
        Creates a time-aligned figure from all the elements in the MgList.

        Args:
            dpi (int, optional): Image quality of the rendered figure in DPI. Defaults to 300.
            autoshow (bool, optional): Whether to show the resulting figure automatically. Defaults to True.
            title (str, optional): Optionally add a title to the figure. Defaults to None (no title).
            export_png (bool, optional): Whether to export a png image of the resulting figure automatically. Defaults to True.

        Returns:
            MgFigure: The MgFigure with all the elements from the MgList as layers.
        """
        import os
        import librosa
        import librosa.display
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        import matplotlib
        import numpy as np

        there_were_layers, first_slot_was_img, img_to_redo = None, None, None

        def count_elems(elems_list, elem_count):
            """
            Counts the all elements in a list recursively.

            Args:
                elems_list (list): The list to count.
                elem_count (int): The current count. (Pass 0 on the top level.)

            Returns:
                int: The number of elements in `elems_list`.
            """
            _count = elem_count

            for obj in elems_list:
                if type(obj) == MgImage:
                    _count += 1

                elif type(obj) == MgFigure:
                    if obj.figure_type == 'audio.tempogram':
                        _count += 2
                    elif obj.figure_type == 'audio.descriptors':
                        _count += 3
                    elif obj.figure_type == 'audio.spectrogram':
                        _count += 1
                    elif obj.figure_type == 'layers':
                        _count = count_elems(obj.layers, _count)

                elif type(obj) == MgList:
                    _count = count_elems(obj.objectlist, _count)

            return _count

        elem_count = count_elems(self.objectlist, 0)

        def build_figure(elems_list, elem_count, fig, ax, index_of_first_plot, plot_counter, of):
            """
            Recursively crawls through the list of objects, and builds a single top-level figure from them.

            Args:
                elems_list (list): List of MgImage, MgFigure or MgList objects.
                elem_count (int): The total number of subplots to make.
                fig (matplotlib.pyplot.figure): The figure to fill.
                ax (list): The list of subplots (or their placeholders).
                index_of_first_plot (int): The index of the first plot.
                plot_counter (int): The running count of subplots (increments while crawling through all levels and building layers).
                of (str): The "running" string for the final output file name (each subplot increments it). 

            Returns:
                str: The final output file name in the current level.
                int: The final count of subplots including the current level.
                bool: Whether there were deeper levels inside the current one.
                bool: Whether the first slot in the figure will come from an MgImage.
                str: The path to the image from the MgImage on the first slot.
            """

            there_were_layers, first_slot_was_img, img_to_redo = None, None, None

            for obj in elems_list:
                if type(obj) == MgImage:
                    if plot_counter == 0:
                        first_slot_was_img = True
                        img_to_redo = obj.filename
                    ax[plot_counter] = fig.add_subplot(
                        elem_count, 1, plot_counter+1)
                    ax[plot_counter].imshow(mpimg.imread(obj.filename))
                    ax[plot_counter].set_aspect('auto')
                    ax[plot_counter].axes.xaxis.set_visible(False)
                    ax[plot_counter].axes.yaxis.set_visible(False)

                    # add title based on content
                    last_tag = os.path.splitext(obj.filename)[0].split('_')[-1]
                    if last_tag == 'mgx':
                        ax[plot_counter].set(title='Motiongram X')
                    elif last_tag == 'mgy':
                        ax[plot_counter].set(title='Motiongram Y')
                    elif last_tag == 'vgx':
                        ax[plot_counter].set(title='Videogram X')
                    elif last_tag == 'vgy':
                        ax[plot_counter].set(title='Videogram Y')
                    else:
                        ax[plot_counter].set(
                            title=os.path.basename(obj.filename))

                    # increment output filename
                    if plot_counter == 0:
                        of = os.path.splitext(obj.filename)[0]
                    else:
                        of += '_'
                        of += os.path.splitext(obj.filename)[0].split('_')[-1]

                    plot_counter += 1

                elif type(obj) == MgFigure:
                    first_plot = False
                    if index_of_first_plot == None:
                        index_of_first_plot = plot_counter  # 0-based!
                        first_plot = True

                    if obj.figure_type == 'audio.tempogram':
                        # increment output filename
                        if plot_counter == 0:
                            of = obj.data['of'] + '_tempogram'
                        else:
                            of += '_tempogram'

                        if first_plot:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1)
                        else:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                        # make plot for onset strength
                        ax[plot_counter].plot(
                            obj.data['times'], obj.data['onset_env'], label='Onset strength')
                        ax[plot_counter].label_outer()
                        ax[plot_counter].legend(frameon=True)
                        plot_counter += 1

                        # make plot for tempogram
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                        librosa.display.specshow(obj.data['tempogram'], sr=obj.data['sr'], hop_length=obj.data['hop_size'],
                                                 x_axis='time', y_axis='tempo', cmap='magma', ax=ax[plot_counter])
                        ax[plot_counter].axhline(obj.data['tempo'], color='w', linestyle='--',
                                                 alpha=1, label='Estimated tempo={:g}'.format(obj.data['tempo']))
                        ax[plot_counter].legend(loc='upper right')
                        ax[plot_counter].set(title='Tempogram')
                        plot_counter += 1

                    elif obj.figure_type == 'audio.descriptors':
                        # increment output filename
                        if plot_counter == 0:
                            of = obj.data['of'] + '_descriptors'
                        else:
                            of += '_descriptors'

                        if first_plot:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1)
                        else:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                        # make plot for rms
                        ax[plot_counter].semilogy(
                            obj.data['times'], obj.data['rms'][0], label='RMS Energy')
                        ax[plot_counter].legend(loc='upper right')
                        plot_counter += 1

                        # make plot for flatness
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                        ax[plot_counter].plot(
                            obj.data['times'], obj.data['flatness'].T, label='Flatness', color='y')
                        ax[plot_counter].legend(loc='upper right')
                        plot_counter += 1

                        # make plot for spectrogram, centroid, bandwidth and rolloff
                        ax[plot_counter] = fig.add_subplot(
                            elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])
                        librosa.display.specshow(librosa.power_to_db(obj.data['S'], ref=np.max, top_db=120), sr=obj.data['sr'],
                                                 y_axis='mel', fmax=obj.data['sr']/2, x_axis='time', hop_length=obj.data['hop_size'], ax=ax[plot_counter])
                        # get rid of "default" ticks
                        ax[plot_counter].yaxis.set_minor_locator(
                            matplotlib.ticker.NullLocator())
                        plot_xticks = np.arange(
                            0, obj.data['length']+0.1, obj.data['length']/20)
                        ax[plot_counter].set(xticks=plot_xticks)

                        freq_ticks = [elem*100 for elem in range(10)]
                        freq_ticks = [250]
                        freq = 500
                        while freq < obj.data['sr']/2:
                            freq_ticks.append(freq)
                            freq *= 1.5

                        freq_ticks = [round(elem, -1) for elem in freq_ticks]
                        freq_ticks_labels = [str(round(
                            elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

                        ax[plot_counter].set(yticks=(freq_ticks))
                        ax[plot_counter].set(yticklabels=(freq_ticks_labels))

                        ax[plot_counter].fill_between(obj.data['times'], obj.data['cent'][0] - obj.data['spec_bw']
                                                      [0], obj.data['cent'][0] + obj.data['spec_bw'][0], alpha=0.5, label='Centroid +- bandwidth')
                        ax[plot_counter].plot(
                            obj.data['times'], obj.data['cent'].T, label='Centroid', color='y')
                        ax[plot_counter].plot(
                            obj.data['times'], obj.data['rolloff'][0], label='Roll-off frequency (0.99)')
                        ax[plot_counter].plot(
                            obj.data['times'], obj.data['rolloff_min'][0], color='r', label='Roll-off frequency (0.01)')

                        ax[plot_counter].legend(loc='upper right')

                        plot_counter += 1

                    elif obj.figure_type == 'audio.spectrogram':
                        # increment output filename
                        if plot_counter == 0:
                            of = obj.data['of'] + '_spectrogram'
                        else:
                            of += '_spectrogram'

                        if first_plot:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1)
                        else:
                            ax[plot_counter] = fig.add_subplot(
                                elem_count, 1, plot_counter+1, sharex=ax[index_of_first_plot])

                        librosa.display.specshow(librosa.power_to_db(obj.data['S'], ref=np.max, top_db=120), sr=obj.data['sr'],
                                                 y_axis='mel', fmax=obj.data['sr']/2, x_axis='time', hop_length=obj.data['hop_size'], ax=ax[plot_counter])
                        # get rid of "default" ticks
                        ax[plot_counter].yaxis.set_minor_locator(
                            matplotlib.ticker.NullLocator())
                        plot_xticks = np.arange(
                            0, obj.data['length']+0.1, obj.data['length']/20)
                        ax[plot_counter].set(xticks=plot_xticks)

                        freq_ticks = [elem*100 for elem in range(10)]
                        freq_ticks = [250]
                        freq = 500
                        while freq < obj.data['sr']/2:
                            freq_ticks.append(freq)
                            freq *= 1.5

                        freq_ticks = [round(elem, -1) for elem in freq_ticks]
                        freq_ticks_labels = [str(round(
                            elem/1000, 1)) + 'k' if elem > 1000 else int(round(elem)) for elem in freq_ticks]

                        ax[plot_counter].set(yticks=(freq_ticks))
                        ax[plot_counter].set(yticklabels=(freq_ticks_labels))
                        ax[plot_counter].set(title='Spectrogram')

                        plot_counter += 1

                    elif obj.figure_type == 'layers':
                        there_were_layers = True
                        if plot_counter == 0:
                            of, plot_counter, _, first_slot_was_img, img_to_redo = build_figure(
                                obj.layers, elem_count, fig, ax, index_of_first_plot, plot_counter, of)
                        else:
                            of, plot_counter, _, _, _ = build_figure(
                                obj.layers, elem_count, fig, ax, index_of_first_plot, plot_counter, of)

                elif type(obj) == MgList:
                    of, plot_counter, _, _, _ = build_figure(
                        obj.objectlist, elem_count, fig, ax, index_of_first_plot, plot_counter, of)

            return of, plot_counter, there_were_layers, first_slot_was_img, img_to_redo

        fig = plt.figure(dpi=dpi, figsize=(10, 3*elem_count))

        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)

        if title != None and type(title)==str:
            # add title
            fig.suptitle(title, fontsize=16, y=0.99)

        ax = [None for elem in range(elem_count)]
        index_of_first_plot = None
        plot_counter = 0
        of = None

        of, plot_counter, there_were_layers, first_slot_was_img, img_to_redo = build_figure(
            self.objectlist, elem_count, fig, ax, index_of_first_plot, plot_counter, of)

        # workaround matplotlib bug: if there was a layered figure where the first slot shows an image, delete and redo that slot
        if first_slot_was_img and there_were_layers:
            ax[0].remove()
            ax[0] = fig.add_subplot(elem_count, 1, 1)
            ax[0].imshow(mpimg.imread(img_to_redo))
            ax[0].set_aspect('auto')
            ax[0].axes.xaxis.set_visible(False)
            ax[0].axes.yaxis.set_visible(False)

            # add title based on content
            last_tag = os.path.splitext(img_to_redo)[0].split('_')[-1]
            if last_tag == 'mgx':
                ax[0].set(title='Motiongram X')
            elif last_tag == 'mgy':
                ax[0].set(title='Motiongram Y')
            elif last_tag == 'vgx':
                ax[0].set(title='Videogram X')
            elif last_tag == 'vgy':
                ax[0].set(title='Videogram Y')
            else:
                ax[0].set(title=os.path.basename(img_to_redo))

        fig.tight_layout()

        # save figure as png
        if export_png:
            plt.savefig(of + '.png', format='png', transparent=False)

        if not autoshow:
            plt.close()

        # create MgFigure
        mgf = MgFigure(
            figure=fig,
            figure_type='layers',
            data=None,
            layers=self.objectlist,
            image=of + '.png'
        )

        return mgf
