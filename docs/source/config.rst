config module
=============

.. automodule:: config
   :members:
   :undoc-members:
   :show-inheritance:


# rst file
.. if-builder:: simplepdf

   .. toctree::

      my_files
      specific_pdf_file

.. if-builder:: html

   .. toctree::

      my_files

   Other HTML specific content, which will not be part of the PDF.