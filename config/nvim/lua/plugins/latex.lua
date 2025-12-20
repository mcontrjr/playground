return {
  -- VimTeX - Best LaTeX plugin for Neovim
  {
    "lervag/vimtex",
    lazy = false, -- lazy-loading will disable inverse search
    config = function()
      -- PDF viewer configuration for Arch Linux
      vim.g.vimtex_view_method = "zathura"

      -- Compiler configuration
      vim.g.vimtex_compiler_method = "latexmk"
      vim.g.vimtex_compiler_latexmk = {
        build_dir = "",
        callback = 1,
        continuous = 1,
        executable = "latexmk",
        options = {
          "-pdf",
          "-verbose",
          "-file-line-error",
          "-synctex=1",
          "-interaction=nonstopmode",
        },
      }

      -- Quickfix window behavior
      vim.g.vimtex_quickfix_mode = 0

      -- Disable some features for better performance
      vim.g.vimtex_indent_enabled = 0
      vim.g.vimtex_syntax_enabled = 1

      -- Concealment (optional - hides LaTeX commands for cleaner view)
      vim.g.vimtex_syntax_conceal_disable = 0
    end,
  },

  -- Treesitter for LaTeX syntax highlighting
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      if type(opts.ensure_installed) == "table" then
        vim.list_extend(opts.ensure_installed, { "latex", "bibtex" })
      end
    end,
  },

  -- LSP support for LaTeX
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        texlab = {
          keys = {
            { "<leader>K", "<plug>(vimtex-doc-package)", desc = "Vimtex Docs", silent = true },
          },
        },
      },
    },
  },
}
