import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChefHat, Plus, Save, Trash2, X } from 'lucide-react';

import api from '../services/api';
import { useActiveRestaurant } from '../hooks/useActiveRestaurant';
import { Card } from '../ui/Card';
import { EmptyState } from '../ui/EmptyState';
import { Skeleton } from '../ui/Skeleton';
import { asArray, decimal, getErrorMessage, money, text, toNumber } from '../utils/format';

export default function Recipes() {
    const activeRestaurant = useActiveRestaurant();
    const [ingredients, setIngredients] = useState([]);
    const [recipes, setRecipes] = useState([]);
    const [menuItems, setMenuItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notice, setNotice] = useState(null);

    // Ingredient form
    const [newIngredient, setNewIngredient] = useState({ name: '', unit: 'kg', cost_per_unit: '' });
    const [savingIngredient, setSavingIngredient] = useState(false);

    // Recipe builder
    const [selectedItem, setSelectedItem] = useState('');
    const [draftLines, setDraftLines] = useState([]); // [{ingredient_id, quantity}]
    const [savingRecipe, setSavingRecipe] = useState(false);

    const query = `restaurant_name=${encodeURIComponent(activeRestaurant)}`;

    const fetchAll = useCallback(async () => {
        if (!activeRestaurant) {
            setIngredients([]); setRecipes([]); setMenuItems([]); setLoading(false);
            return;
        }
        setLoading(true);
        try {
            const [ingredientRes, recipeRes, classificationRes] = await Promise.all([
                api.get(`/recipes/ingredients?${query}`),
                api.get(`/recipes?${query}`),
                api.get(`/analytics/classification?${query}`),
            ]);
            setIngredients(asArray(ingredientRes.data));
            setRecipes(asArray(recipeRes.data));
            setMenuItems(asArray(classificationRes.data).sort((a, b) => text(a?.item_name, '').localeCompare(text(b?.item_name, ''))));
            setError(null);
        } catch (err) {
            setError(getErrorMessage(err, 'Failed to load recipe data.'));
        } finally {
            setLoading(false);
        }
    }, [activeRestaurant, query]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const recipeByItem = useMemo(() => {
        const map = {};
        recipes.forEach((r) => { map[r?.item_name] = r; });
        return map;
    }, [recipes]);

    // Load the selected item's saved recipe into the draft editor.
    useEffect(() => {
        const saved = recipeByItem[selectedItem];
        setDraftLines(saved ? asArray(saved.lines).map((l) => ({ ingredient_id: l.ingredient_id, quantity: String(l.quantity) })) : []);
    }, [selectedItem, recipeByItem]);

    const flash = (message) => { setNotice(message); setTimeout(() => setNotice(null), 4000); };

    const addIngredient = async (e) => {
        e.preventDefault();
        setSavingIngredient(true);
        try {
            await api.post(`/recipes/ingredients?${query}`, {
                name: newIngredient.name.trim(),
                unit: newIngredient.unit.trim() || 'unit',
                cost_per_unit: toNumber(newIngredient.cost_per_unit),
            });
            setNewIngredient({ name: '', unit: 'kg', cost_per_unit: '' });
            await fetchAll();
            flash('Ingredient added.');
        } catch (err) {
            setError(getErrorMessage(err, 'Could not add the ingredient.'));
        } finally {
            setSavingIngredient(false);
        }
    };

    const updateIngredientCost = async (ingredient, cost) => {
        try {
            await api.put(`/recipes/ingredients/${ingredient.id}`, {
                name: ingredient.name, unit: ingredient.unit, cost_per_unit: toNumber(cost),
            });
            await fetchAll();
            flash(`Updated ${ingredient.name} — all recipe margins recalculated.`);
        } catch (err) {
            setError(getErrorMessage(err, 'Could not update the ingredient.'));
        }
    };

    const removeIngredient = async (ingredient) => {
        try {
            await api.delete(`/recipes/ingredients/${ingredient.id}`);
            await fetchAll();
        } catch (err) {
            setError(getErrorMessage(err, 'Could not delete the ingredient.'));
        }
    };

    const saveRecipe = async () => {
        const lines = draftLines
            .filter((l) => l.ingredient_id && toNumber(l.quantity) > 0)
            .map((l) => ({ ingredient_id: Number(l.ingredient_id), quantity: toNumber(l.quantity) }));
        if (!selectedItem || lines.length === 0) return;
        setSavingRecipe(true);
        try {
            await api.put(`/recipes/items/${encodeURIComponent(selectedItem)}?${query}`, { lines });
            await fetchAll();
            flash(`Recipe saved — ${selectedItem} now uses ingredient-level cost in all analytics.`);
        } catch (err) {
            setError(getErrorMessage(err, 'Could not save the recipe.'));
        } finally {
            setSavingRecipe(false);
        }
    };

    const removeRecipe = async () => {
        if (!selectedItem || !recipeByItem[selectedItem]) return;
        setSavingRecipe(true);
        try {
            await api.delete(`/recipes/items/${encodeURIComponent(selectedItem)}?${query}`);
            await fetchAll();
            flash(`Recipe removed — ${selectedItem} reverts to its uploaded cost.`);
        } catch (err) {
            setError(getErrorMessage(err, 'Could not remove the recipe.'));
        } finally {
            setSavingRecipe(false);
        }
    };

    const draftCost = draftLines.reduce((sum, line) => {
        const ingredient = ingredients.find((i) => i.id === Number(line.ingredient_id));
        return sum + (ingredient ? toNumber(line.quantity) * toNumber(ingredient.cost_per_unit) : 0);
    }, 0);

    const selectedMenuItem = menuItems.find((m) => m?.item_name === selectedItem);

    return (
        <div className="space-y-7">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-ink-900 rounded-lg shadow-sm flex items-center justify-center">
                    <ChefHat className="w-6 h-6 text-primary-100" />
                </div>
                <div>
                    <p className="text-xs font-bold uppercase tracking-[0.24em] text-primary-700">True cost engine</p>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight mt-1">Recipes & Costs</h1>
                    <p className="text-slate-500 text-sm mt-1">
                        Define what goes into each dish. Items with a recipe use live ingredient prices in every margin calculation — update one price and all analytics follow.
                    </p>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 shadow-sm">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <p className="text-sm text-red-700 font-semibold">{error}</p>
                    <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-700"><X className="w-4 h-4" /></button>
                </div>
            )}
            {notice && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm font-semibold text-emerald-800 shadow-sm">{notice}</div>
            )}

            {!activeRestaurant ? (
                <EmptyState title="No restaurant selected" message="Upload a sales file first, then cost its menu here." />
            ) : loading ? (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {[1, 2].map((i) => (
                        <Card key={i} animate={false} className="p-6 space-y-4">
                            {[1, 2, 3, 4].map((j) => <Skeleton key={j} className="h-10 w-full" />)}
                        </Card>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
                    {/* ------------------------- Ingredients ------------------------- */}
                    <Card className="p-6 border-slate-200">
                        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-1">Ingredient Prices</h2>
                        <p className="text-xs text-slate-400 font-semibold mb-5">The price list every recipe draws from.</p>

                        <form onSubmit={addIngredient} className="grid grid-cols-[1.4fr_0.8fr_1fr_auto] gap-2 mb-5">
                            <input
                                type="text" placeholder="Ingredient (e.g. Paneer)" required value={newIngredient.name}
                                onChange={(e) => setNewIngredient((s) => ({ ...s, name: e.target.value }))}
                                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300"
                            />
                            <input
                                type="text" placeholder="Unit" required value={newIngredient.unit}
                                onChange={(e) => setNewIngredient((s) => ({ ...s, unit: e.target.value }))}
                                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300"
                            />
                            <input
                                type="number" step="0.01" min="0" placeholder="Cost / unit" required value={newIngredient.cost_per_unit}
                                onChange={(e) => setNewIngredient((s) => ({ ...s, cost_per_unit: e.target.value }))}
                                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300"
                            />
                            <button type="submit" disabled={savingIngredient}
                                className="inline-flex items-center gap-1 rounded-md bg-ink-900 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-ink-800 disabled:opacity-40">
                                <Plus className="w-4 h-4" /> Add
                            </button>
                        </form>

                        {ingredients.length === 0 ? (
                            <p className="text-sm text-slate-400 py-6 text-center">No ingredients yet. Add your first one above.</p>
                        ) : (
                            <div className="divide-y divide-slate-100">
                                {ingredients.map((ingredient) => (
                                    <IngredientRow
                                        key={ingredient.id}
                                        ingredient={ingredient}
                                        onSaveCost={(cost) => updateIngredientCost(ingredient, cost)}
                                        onDelete={() => removeIngredient(ingredient)}
                                    />
                                ))}
                            </div>
                        )}
                    </Card>

                    {/* ------------------------- Recipe builder ------------------------- */}
                    <Card className="p-6 border-slate-200">
                        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-1">Recipe Builder</h2>
                        <p className="text-xs text-slate-400 font-semibold mb-5">
                            Amounts are per one unit sold. {recipes.length} item(s) currently costed by recipe.
                        </p>

                        <label className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Menu item</label>
                        <select
                            value={selectedItem}
                            onChange={(e) => setSelectedItem(e.target.value)}
                            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-300 mb-4"
                        >
                            <option value="">Select an item from your sales data…</option>
                            {menuItems.map((m) => (
                                <option key={text(m?.item_name)} value={m?.item_name}>
                                    {text(m?.item_name)}{recipeByItem[m?.item_name] ? ' ✓ (has recipe)' : ''}
                                </option>
                            ))}
                        </select>

                        {selectedItem && (
                            <>
                                <div className="space-y-2 mb-4">
                                    {draftLines.map((line, index) => {
                                        const ingredient = ingredients.find((i) => i.id === Number(line.ingredient_id));
                                        return (
                                            <div key={index} className="grid grid-cols-[1.5fr_1fr_auto_auto] gap-2 items-center">
                                                <select
                                                    value={line.ingredient_id}
                                                    onChange={(e) => setDraftLines((lines) => lines.map((l, i) => i === index ? { ...l, ingredient_id: e.target.value } : l))}
                                                    className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none"
                                                >
                                                    <option value="">Ingredient…</option>
                                                    {ingredients.map((i) => <option key={i.id} value={i.id}>{i.name} ({money(i.cost_per_unit)}/{i.unit})</option>)}
                                                </select>
                                                <input
                                                    type="number" step="0.001" min="0" placeholder={`Qty${ingredient ? ` (${ingredient.unit})` : ''}`}
                                                    value={line.quantity}
                                                    onChange={(e) => setDraftLines((lines) => lines.map((l, i) => i === index ? { ...l, quantity: e.target.value } : l))}
                                                    className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none"
                                                />
                                                <span className="text-xs font-bold text-slate-500 tabular-nums w-20 text-right">
                                                    {ingredient ? money(toNumber(line.quantity) * toNumber(ingredient.cost_per_unit)) : '—'}
                                                </span>
                                                <button onClick={() => setDraftLines((lines) => lines.filter((_, i) => i !== index))}
                                                    className="text-slate-300 hover:text-red-600" aria-label="Remove line">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>

                                <button
                                    onClick={() => setDraftLines((lines) => [...lines, { ingredient_id: '', quantity: '' }])}
                                    className="inline-flex items-center gap-1.5 text-xs font-bold text-primary-700 hover:text-primary-800 mb-5"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Add ingredient line
                                </button>

                                <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4 mb-4">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Recipe cost / unit</span>
                                        <span className="font-black text-slate-900 tabular-nums">{money(draftCost)}</span>
                                    </div>
                                    {selectedMenuItem && (
                                        <div className="flex items-center justify-between text-xs mt-2 text-slate-500 font-semibold">
                                            <span>Uploaded avg cost: {money(selectedMenuItem.unit_cost)} · Avg price: {money(toNumber(selectedMenuItem.total_revenue) / Math.max(1, toNumber(selectedMenuItem.total_quantity)))}</span>
                                            <span className={draftCost > 0 ? 'text-emerald-700' : ''}>
                                                {draftCost > 0 ? `Margin @ recipe cost: ${decimal(100 * (1 - draftCost / Math.max(0.01, toNumber(selectedMenuItem.total_revenue) / Math.max(1, toNumber(selectedMenuItem.total_quantity)))), 1)}%` : ''}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="flex gap-3">
                                    <button
                                        onClick={saveRecipe}
                                        disabled={savingRecipe || draftLines.every((l) => !l.ingredient_id || toNumber(l.quantity) <= 0)}
                                        className="inline-flex items-center gap-1.5 rounded-md bg-ink-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-ink-800 disabled:opacity-40"
                                    >
                                        <Save className="w-4 h-4" /> {savingRecipe ? 'Saving…' : 'Save recipe'}
                                    </button>
                                    {recipeByItem[selectedItem] && (
                                        <button onClick={removeRecipe} disabled={savingRecipe}
                                            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-red-600 hover:text-red-800 disabled:opacity-40">
                                            <Trash2 className="w-4 h-4" /> Remove recipe
                                        </button>
                                    )}
                                </div>
                            </>
                        )}

                        {!selectedItem && menuItems.length === 0 && (
                            <p className="text-sm text-slate-400 py-4">Upload sales data first — menu items come from your sales records.</p>
                        )}
                    </Card>
                </div>
            )}
        </div>
    );
}

function IngredientRow({ ingredient, onSaveCost, onDelete }) {
    const [cost, setCost] = useState(String(ingredient.cost_per_unit));
    const dirty = toNumber(cost) !== toNumber(ingredient.cost_per_unit);

    return (
        <div className="flex items-center gap-3 py-2.5">
            <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-slate-800 truncate">{text(ingredient.name)}</p>
                <p className="text-xs text-slate-400 font-semibold">per {text(ingredient.unit)}</p>
            </div>
            <input
                type="number" step="0.01" min="0" value={cost}
                onChange={(e) => setCost(e.target.value)}
                className="w-28 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-right tabular-nums text-slate-700 shadow-sm focus:border-primary-400 focus:outline-none"
                aria-label={`Cost per ${ingredient.unit} of ${ingredient.name}`}
            />
            {dirty && (
                <button onClick={() => onSaveCost(cost)} className="text-primary-700 hover:text-primary-900" aria-label="Save cost">
                    <Save className="w-4 h-4" />
                </button>
            )}
            <button onClick={onDelete} className="text-slate-300 hover:text-red-600" aria-label={`Delete ${ingredient.name}`}>
                <Trash2 className="w-4 h-4" />
            </button>
        </div>
    );
}
