-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Shortcut for I->N
vim.api.nvim_set_keymap("i", "jj", "<Esc>", { noremap = false })
vim.api.nvim_set_keymap("n", "<C-a>", ":%y<Enter>", { noremap = false })
vim.api.nvim_set_keymap("n", ":qa", ":quitall", {})
